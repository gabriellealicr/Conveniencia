from django.shortcuts import redirect

def redirect_if_authenticated(view_func):
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:       # Verifica se o usuário está autenticado
            return redirect('pagina_inicial')   # Redireciona para a página inicial
        else:
            return view_func(request, *args, **kwargs)  # Caso não, retorna para a página de login como solicitado

    return wrapper   # Retorna a função acima
