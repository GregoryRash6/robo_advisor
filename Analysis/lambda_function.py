# Import Dependencies
from datetime import datetime
from dateutil.relativedelta import relativedelta
from botocore.vendored import requests

# Helper Function to Convert to Integer
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """

    # Try to Convert 
    try:

        # Convert to Integer 
        return int(n)

    # Handle Errors 
    except ValueError:

        # Return NaN 
        return float("nan")

# Function to Recommend Investment Strategy
def risk(risk_level):
    """
    Defines each risk level
    """

    # Handle No Risk Tolerance
    if risk_level == "None":

        # Recommend Most Conservative Strategy 
        recommend = "100% bonds (AGG), 0% equities (SPY)"

    # Handle Very Low Risk Tolerance 
    elif risk_level == "Very Low":

        # Recommend Very Conservative Strategy 
        recommend = "80% bonds (AGG), 20% equities (SPY)"

    # Handle Low Risk Tolerance 
    elif risk_level == "Low":

        # Recommend Conservative Strategy 
        recommend = "60% bonds (AGG), 40% equities (SPY)"

    # Handle Moderate Risk Tolerance 
    elif risk_level == "Medium":

        # Recommend Moderate Strategy 
        recommend = "40% bonds (AGG), 60% equities (SPY)"

    # Handle High Risk Tolerance 
    elif risk_level == "High":

        # Recommend Liberal Strategy 
        recommend = "20% bonds (AGG), 80% equities (SPY)"

    # Handle Very High Risk Tolerance 
    else:

        # Recommend Very Liberal Strategy 
        recommend = "0% bonds (AGG), 100% equities (SPY)"

    # Return Recommendation
    return recommend

# Create Lex Response Function 
def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """

    # Handle Missing Message 
    if message_content is None:

        # Return Lex Response 
        return {"isValid": is_valid, "violatedSlot": violated_slot}

    # Return Valid Lex Response 
    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

# Build Input Validation Function 
def validate_data(age, investment_amount, intent_request):
    """
    Validates the data provided by the user.
    """
    # Handle Age Validation
    if age is not None:

        # Call Helper Function 
        age = parse_int(age)
        
        # Handle Ages Out of Range
        if age<=21 or age>65:

            # Call Lex Response Function 
            return build_validation_result(
                                False,
                                "age",
                                "You need to be older than 21 and less than 65 to utilize this service."
                                "Please provide your proper age."
                                )
    
    # Handle Investment Amount Validation 
    if investment_amount is not None:

        # Call Helper Function 
        investment_amount = parse_int(investment_amount) 
    
        # Handle When Investment Amount is too Low 
        if investment_amount<5000:

            # Call Lex Response Function 
            return build_validation_result(
                False,
                "investmentAmount",
                "This service is only available for investments over $5000."
                "Please provide a proper amount"
                )
            
    # Return True with Valid Response
    return build_validation_result(True, None, None)

# Function to Get Slots 
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """

    # Return Slots 
    return intent_request["currentIntent"]["slots"]


# Function to Define Elicit Slot Type 
def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """

    # Return Proper Response 
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }


# Function to Delegate Slot Type 
def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """

    # Return Delegation 
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }


# Function to Define Close Slot Type 
def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """

    # Formulate Response 
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }

    # Return Response 
    return response


# Function to Recommend Portfolio 
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """

    # Save First Name 
    first_name = get_slots(intent_request)["firstName"]

    # Save Age 
    age = get_slots(intent_request)["age"]

    # Save Investment Amount 
    investment_amount = get_slots(intent_request)["investmentAmount"]

    # Save Risk Tolerance 
    risk_level = get_slots(intent_request)["riskLevel"]

    # Save Source 
    source = intent_request["invocationSource"]

    # Initialization & Validation 
    if source == "DialogCodeHook":
        
        # Get All Slots
        slots = get_slots(intent_request)

        # Validate Data 
        validation_result = validate_data(age, investment_amount, intent_request)
        
        # Handle Invalid Data
        if not validation_result["isValid"]:

            # Clean Invalid Slot 
            slots[validation_result["violatedSlot"]] = None 

            # Returns elicitSlot Dialog to Request New Data for the Invalid Slot
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )

        # Fetch Current Session Attibutes
        output_session_attributes = intent_request["sessionAttributes"]

        # Return Delegation 
        return delegate(output_session_attributes, get_slots(intent_request))

    # Get Initial Investment Recommendation
    initial_recommendation = risk(risk_level) 
   

    # Return Initial Recommendation Message
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} thank you for your information;
            based on the risk level you defined, my recommendation is to choose an investment portfolio with {}
            """.format(
                first_name, initial_recommendation
            ),
        },
    )


# Function to Dispatch Intent 
def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    # Save Intent Name 
    intent_name = intent_request["currentIntent"]["name"]

    # Dispatch to Bot's Intent Handlers
    if intent_name == "RecommendPortfolio":

        # Return Portfolio Recommendation 
        return recommend_portfolio(intent_request)

    # Handle Errors 
    raise Exception("Intent with name " + intent_name + " not supported")

# Function to Handle Lambda
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """

    # Return Dispatch Event 
    return dispatch(event)