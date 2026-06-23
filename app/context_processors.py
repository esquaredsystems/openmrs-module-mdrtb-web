def locale(request):
    return {"locale": request.session.get("locale", "ru")}
