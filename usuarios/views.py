from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
import logging 
logger = logging.getLogger()
from .decorators import redirect_if_authenticated
import re
from django.contrib import messages

@redirect_if_authenticated  # Verifica se o usuário já está logado, caso sim, redirecionar para a página inicial
def Login(request):
    if request.method == "POST": # Quando o método é POST, ou seja, ao clicar no botão "Salvar", que é um submit
        usuario = request.POST.get("usuario")
        senha = request.POST.get("senha")
        try:
            usuario_sistema = authenticate(request, username=usuario, password=senha) # Autentica o usuário
            if usuario_sistema is not None: # Verifica se o usuário existe
                login(request, usuario_sistema)
                return redirect('pagina_inicial' )
            else:
                raise Exception("Usuário e/ou senha informados incorretamente!")
        except Exception as e:
            if str(e) == "Usuário e/ou senha informados incorretamente!":
                try:
                    User.objects.get(username=usuario)  
                    mensagem_erro = "Usuário e/ou senha informados incorretamente!"
                except User.DoesNotExist:
                    mensagem_erro = "Usuário não cadastrado."
                return render(request, "usuarios/login.html", {"erro": mensagem_erro, "campo_foco": "usuario"})
    else:         # Quando o método não é POST, ou seja, entrando no formulário para cadastrar
        return render(request, "usuarios/login.html")
    
def Logout(request):    # Realiza o logout, redirecionando para a paǵina de login
    request.session.flush()
    return redirect('login')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Cadastro(request):
    if request.method == "POST":         
        usuario_usuario = request.POST.get('usuario_usuario')
        email_usuario = request.POST.get('email')
        senha_usuario = request.POST.get('senha')
        conf_usuario = request.POST.get('conf_senha')

        usuario_espaco = usuario_usuario.strip()
        if usuario_espaco == '':     
            messages.error(request, 'Insira um nome de usuário válido.', extra_tags='erro_usuario')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        user = User.objects.filter(username=usuario_usuario).first()  # Busca o usuário digitado
        if user:  # Verifica se o usuário existe
            messages.error(request, 'Usuário já cadastrado.', extra_tags='erro_usuario_cad')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        user = User.objects.filter(email=email_usuario).first()       # Busca o e-mail digitado
        if user:  # Verifica se o e-mail existe
            messages.error(request, 'E-mail já cadastrado.', extra_tags='erro_email')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email_usuario):  # Verifica se o email possui o formato adequado
            messages.error(request, 'Insira um e-mail válido.', extra_tags='erro_email')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
        if senha_usuario == conf_usuario:   # Se as senhas coincidem
            user = User.objects.create_user(username=usuario_usuario, email=email_usuario, password=senha_usuario)  
            user.save()
            url = reverse('visualizar_usuarios') 
            url += f'?sucesso_cadastro=Usuário cadastrado com sucesso!'
            return redirect(url) 
        else:                               # Se as senhas não coincidem
            messages.error(request, 'Senhas não coincidem.', extra_tags='erro_senha')
            url = reverse('cadastrar_usuario')
            url += f'?usuario_usuario={usuario_usuario}&email={email_usuario}'
            return redirect(url)
    else:     
        return render(request, "usuarios/cadastro.html", {"campo_foco": "usuario_usuario"})

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Visualizar(request):
    sucesso_cadastro = request.GET.get('sucesso_cadastro')
    if request.user.is_authenticated:  
        usuario = request.user
    usuarios_sistema = User.objects.all()
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

@user_passes_test(lambda u: u.is_superuser, login_url='login')    
def Alterar(request, usuario_id):         # Função após o "Salvar" na função Acessar
    if request.user.is_authenticated:    
        usuario = request.user
    user = get_object_or_404(User, id=usuario_id)  
    if request.method == "POST":         
        user.username  = request.POST['usuario']
        user.email  = request.POST['email']
        user_cadastrado = User.objects.filter(username=user.username).exclude(id=usuario_id) # Busca o usuário digitado
        usuario_espaco = user.username.strip()
        if usuario_espaco == '':    
            messages.error(request, 'Insira um nome de usuário válido.', extra_tags='erro_usuario')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        if user_cadastrado.exists():
            messages.error(request, 'Usuário já cadastrado.', extra_tags='erro_usuario')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        email_cadastrado = User.objects.filter(email=user.email).exclude(id=usuario_id)  # Busca o e-mail digitado
        if email_cadastrado.exists():
            messages.error(request, 'E-mail já cadastrado.', extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', user.email):
            messages.error(request, 'Insira um e-mail válido.', extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
        try:
            user.save()
            redirect_url = reverse('visualizar_usuarios') + '?sucesso_cadastro=Usuário editado com sucesso!'
            return redirect(redirect_url)
        except:
            messages.error(request, 'Erro de edição.', extra_tags='erro_email')
            url = reverse('acessar_usuario', args=[usuario_id])
            url += f'?user={user}'
            return redirect(url)
    else:
        return render(request, "usuarios/acessar.html", {"user": user, "usuario": usuario})

@user_passes_test(lambda u: u.is_superuser, login_url='login')    
def Inativar(request, usuario_id):  # Função para inativar um usuário, setando o is_active como False
    user = get_object_or_404(User, id=usuario_id)
    user.is_active = False
    user.save()
    return redirect('visualizar_usuarios')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Ativar(request, usuario_id):   # Função para ativar um usuário, setando o is_active como True
    user = get_object_or_404(User, id=usuario_id)
    user.is_active = True
    user.save()
    return redirect('visualizar_usuarios')

@user_passes_test(lambda u: u.is_superuser, login_url='login')
def Acessar(request, usuario_id):  # Visualização de edição
    if request.user.is_authenticated:
        usuario = request.user
    user = User.objects.get(id=usuario_id)
    return render(request, 'usuarios/acessar.html',{'user': user, "usuario": usuario})

