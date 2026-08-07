def generate_reason(feature, value):

    if feature == "gst_filing_regularity":
        return f"GST filing regularity is {value}%."

    elif feature == "bounce_frequency":
        return f"Bounce frequency is {value}, affecting credit confidence."

    elif feature == "business_age_years":
        return f"Business has operated for {value} years."

    elif feature == "avg_monthly_balance":
        return f"Average monthly balance is ₹{value:,}."

    elif feature == "income_stability":
        return f"Income stability score is {value}."

    elif feature == "monthly_bank_volume":
        return f"Monthly bank transaction volume is ₹{value:,}."

    elif feature == "loan_default_history":
        if value == 0:
            return "No previous loan defaults."
        return "Previous loan default history reduced the score."

    return f"{feature}: {value}"