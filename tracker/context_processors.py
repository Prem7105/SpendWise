def user_currency(request):
    if request.user.is_authenticated:
        profile = getattr(request.user, "profile", None)
        return {"CURRENCY": getattr(profile,"currency","Rs")}
    return {"CURRENCY":"Rs"}
