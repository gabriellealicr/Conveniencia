from django.contrib import messages
import re
from .decorators import redirect_if_authenticated
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
import logging
logger = logging.getLogger()
from django.views.decorators.cache import never_cache
from django.contrib.auth.hashers import make_password


@never_cache
@redirect_if_authenticated # Verifica se o usuário já está logado, caso sim, redirecionar para a página inicial
def Login(request):
    if request.method == "POST":  # Quando o método é POST, ou seja, ao clicar no botão "Salvar", que é um submit
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        mensagem_erro_cad = ''
        mensagem_erro = ''
        try:
            usuario_sistema = authenticate(
                request, username=usuario, password=senha)  # Autentica o usuário
            if usuario_sistema is not None:  # Verifica se o usuário existe
                login(request, usuario_sistema)
                return redirect('pagina_inicial')
            else:
                raise Exception(
                    "Usuário e/ou senha informados incorretamente!")
        except Exception as e:
            if str(e) == "Usuário e/ou senha informados incorretamente!":
                try:
                    User.objects.get(username=usuario)
                    mensagem_erro = "Usuário e/ou senha informados incorretamente!"
                except User.DoesNotExist:
                    mensagem_erro_cad = "Usuário não cadastrado."
                # return render(request, "usuarios/login.html", {"erro": mensagem_erro, "erro_cad": mensagem_erro_cad, "campo_foco": "usuario"})
                messages.error(request, mensagem_erro, extra_tags='erro')
                messages.error(request, mensagem_erro_cad, extra_tags='erro_cad')
                return redirect('cadastrar_usuario')
    else:         # Quando o método não é POST, ou seja, entrando no formulário para cadastrar
        return render(request, "usuarios/login.html")


@never_cache
def Logout(request):    # Realiza o logout, redirecionando para a paǵina de login
    # request.session.flush()
    logout(request)
    return redirect('login')


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Cadastro(request):
    if request.method == "POST":
        usuario_usuario = request.POST.get('usuario_usuario')
        email_usuario = request.POST.get('email')
        senha_usuario = request.POST.get('senha')
        conf_usuario = request.POST.get('conf_senha')

        usuario_espaco = usuario_usuario.strip()
        if usuario_espaco == '':
            messages.error(
                request, 'Insira um usuário válido.', extra_tags='erro_usuario')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        # Busca o usuário digitado
        user = User.objects.filter(username=usuario_usuario).first()
        if user:  # Verifica se o usuário existe
            messages.error(request, 'Usuário já cadastrado.',
                           extra_tags='erro_usuario_cad')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        # Busca o e-mail digitado
        user = User.objects.filter(email=email_usuario).first()
        if user:  # Verifica se o e-mail existe
            messages.error(request, 'E-mail já cadastrado.',
                           extra_tags='erro_email')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        # Verifica se o email possui o formato adequado
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_usuario):
            messages.error(request, 'Insira um e-mail válido.',
                           extra_tags='erro_email')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        if senha_usuario == conf_usuario:   # Se as senhas coincidem
            user = User.objects.create_user(
                username=usuario_usuario, email=email_usuario, password=senha_usuario)
            user.save()
            url = reverse('visualizar_usuarios')
            url += f'?sucesso_cadastro=Usuário cadastrado com sucesso!'
            return redirect(url)
        else:                               # Se as senhas não coincidem
            messages.error(request, 'Senhas não coincidem.',
                           extra_tags='erro_senha')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
    else:
        return render(request, "usuarios/cadastro.html", {"campo_foco": "usuario_usuario"})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Visualizar(request):
    sucesso_cadastro = request.GET.get('sucesso_cadastro')
    if request.user.is_authenticated:
        usuario = request.user
    usuarios_sistema = User.objects.all().order_by('-is_active', 'username')
    inativos = request.GET.get('inativos')
    if inativos:
        usuarios_sistema = User.objects.filter(is_active=False)
    pesquisa = request.GET.get('pesquisa')
    if pesquisa:
        usuarios_sistema = usuarios_sistema.filter(
            username__icontains=pesquisa
        ) | usuarios_sistema.filter(
            email__icontains=pesquisa
        )
    return render(request, "usuarios/visualizar.html", {"usuarios": usuarios_sistema, "usuario": usuario, "sucesso_cadastro": sucesso_cadastro})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Alterar(request, usuario_id):         # Função após o "Salvar" na função Acessar
    if request.user.is_authenticated:
        usuario = request.user
    user = get_object_or_404(User, id=usuario_id)
    if request.method == "POST":
        user.username = request.POST['usuario_usuario']
        user.email = request.POST['email']
        user_cadastrado = User.objects.filter(username=user.username).exclude(
            id=usuario_id)  # Busca o usuário digitado
        usuario_espaco = user.username.strip()
        if usuario_espaco == '':
            messages.error(
                request, 'Insira um usuário válido.', extra_tags='erro_usuario')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        if user_cadastrado:
            messages.error(request, 'Usuário já cadastrado.',
                           extra_tags='erro_usuario')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        email_cadastrado = User.objects.filter(email=user.email).exclude(
            id=usuario_id)  # Busca o e-mail digitado
        if email_cadastrado.exists():
            messages.error(request, 'E-mail já cadastrado.',
                           extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', user.email):
            messages.error(request, 'Insira um e-mail válido.',
                           extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        try:
            user.save()
            redirect_url = reverse('visualizar_usuarios') + \
                '?sucesso_cadastro=Usuário editado com sucesso!'
            return redirect(redirect_url)
        except:
            messages.error(request, 'Erro de edição.', extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
    else:
        return render(request, "usuarios/acessar.html", {"user": user, "usuario": usuario})


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Inativar(request, usuario_id):  # Função para inativar um usuário, setando o is_active como False
    user = get_object_or_404(User, id=usuario_id)
    user.is_active = False
    user.save()
    return redirect('visualizar_usuarios')


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Ativar(request, usuario_id):   # Função para ativar um usuário, setando o is_active como True
    user = get_object_or_404(User, id=usuario_id)
    user.is_active = True
    user.save()
    return redirect('visualizar_usuarios')


@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Acessar(request, usuario_id):  # Visualização de edição
    if request.user.is_authenticated:
        usuario = request.user
    user = User.objects.get(id=usuario_id)
    return render(request, 'usuarios/acessar.html', {'user': user, "usuario": usuario})

@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Acessar_Senha(request, usuario_id):    # Visualização de edição
    if request.user.is_authenticated:
        usuario = request.user
    user = User.objects.get(id=usuario_id)
    return render(request, 'usuarios/acessar_senha.html', {'user': user, "usuario": usuario})

@never_cache
@user_passes_test(lambda u: u.is_superuser, login_url='login')
# Função após o "Salvar" na função Acessar
def Alterar_Senha(request, usuario_id):
    if request.user.is_authenticated:
        usuario = request.user
    user = get_object_or_404(User, id=usuario_id)
    if request.method == "POST":
        senha_usuario = request.POST['senha']
        conf_usuario = request.POST['conf_senha']

        if senha_usuario != conf_usuario:         # Verifica se a senha e confirmação de senha são iguais
            messages.error(request, 'Senhas não coincidem.',
                           extra_tags='erro_senha')
            url = reverse('acessar_usuario_senha', args=[usuario_id])
            url += f'?usuario={usuario_id}'
            return redirect(url)
        else:
            try:
                user.password = make_password(senha_usuario)
                user.save()
                redirect_url = reverse(
                    'visualizar_usuarios') + '?sucesso_cadastro=Senha de usuário editada com sucesso!'
                return redirect(redirect_url)
            except:
                return render(request, "usuarios/acessar.html", {"erro": "Erro de edição"})
    else:
        return render(request, "usuarios/acessar.html", {"usuario": usuario, "user": user})