def user_context(request):
    if request.user.is_authenticated:   # Verifica se o usuário está autenticado como superuser
        return {'usuario': request.user}
    else:
        return {}                    
