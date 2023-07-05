from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from . models import Colaborador
import logging 
logger = logging.getLogger()
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password


@login_required(login_url='login')      
def Cadastro(request):
    if request.method == "POST": # Quando o método é POST, ou seja, ao clicar no botão "Salvar", que é um submit
        nome_colaborador = request.POST.get('nome')
        cpf_colaborador = request.POST.get('cpf')
        login_colaborador = request.POST.get('login')
        senha_colaborador= request.POST.get('senha')
        senha_crip = make_password(senha_colaborador)
        print(senha_crip)
        conf_colaborador = request.POST.get('conf_senha')
        cpf_colaborador = cpf_colaborador.replace('.', '').replace('-', '')

        nome_espaco = nome_colaborador.strip()
        login_espaco = login_colaborador.strip()

        if nome_espaco == '':                             # Verifica se o nome tem apenas espaço
            messages.error(request, 'Insira um nome válido.', extra_tags='erro_nome')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&cpf={cpf_colaborador}&login={login_colaborador}'
            return redirect(url)
        if not Valida_cpf(cpf_colaborador):               # Verifica se o CPF não tem 11 dígitos e não contém apenas números
            messages.error(request, 'Insira um CPF válido.', extra_tags='erro_cpf')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&cpf={cpf_colaborador}&login={login_colaborador}'
            return redirect(url)
        colaborador_login = Colaborador.objects.filter(login=login_colaborador).first() 
        if login_espaco == '':
            messages.error(request, 'Insira um login válido.', extra_tags='erro_login')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&cpf={cpf_colaborador}&login={login_colaborador}'
            return redirect(url)
        if colaborador_login:                             # Verifica a existência do login
            messages.error(request, 'Login já cadastrado.', extra_tags='erro_login')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&cpf={cpf_colaborador}&login={login_colaborador}'
            return redirect(url)
        colaborador_cpf = Colaborador.objects.filter(cpf=cpf_colaborador).first()
        if colaborador_cpf:                               # Verifica a existência do CPF                                                   
            messages.error(request, 'CPF já cadastrado.', extra_tags='erro_cpf')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&login={login_colaborador}&cpf={cpf_colaborador}'
            return redirect(url)
        if senha_colaborador != conf_colaborador:         # Verifica se a senha e confirmação de senha são iguais
            messages.error(request, 'Senhas não coincidem.', extra_tags='erro_senha')
            url = reverse('cadastro_colaborador')
            url += f'?nome={nome_colaborador}&login={login_colaborador}&cpf={cpf_colaborador}&campo_foco={cpf_colaborador}'
            return redirect(url)
        if not colaborador_login and not colaborador_cpf: # Caso não retorne erro, cria o colaborador
            colaborador = Colaborador(nome=nome_colaborador, cpf=cpf_colaborador, login=login_colaborador, senha=senha_crip, ativo=True) 
            # try:
            # colaborador.full_clean()
            colaborador.save()
            url = reverse('visualizar_colaboradores')
            url += f'?sucesso_cadastro=Colaborador cadastrado com sucesso!'
            return redirect(url)
            # except:
            #     messages.error(request, 'Erro de cadastro.', extra_tags='erro_senha')
            #     url = reverse('cadastro_colaborador')
            #     url += f'?nome={nome_colaborador}&login={login_colaborador}&cpf={cpf_colaborador}&campo_foco={cpf_colaborador}'
            #     return redirect(url)
    else:   # Quando o método não é POST, ou seja, entrando no formulário para cadastrar
        return render(request, "colaboradores/cadastro.html", {"campo_foco": "nome"}) 
    
@login_required(login_url='login')
def Visualizar(request):
    sucesso_cadastro = request.GET.get('sucesso_cadastro')
    colaboradores = Colaborador.objects.all()
    inativos = request.GET.get('inativos')
    if inativos:
        colaboradores = colaboradores.filter(ativo=False)
    pesquisa = request.GET.get('pesquisa')
    if pesquisa:
        cpf_pesquisa = pesquisa.replace('.', '').replace('-', '') # Remove caracteres especiais do CPF para permitir pesquisa com ou sem formatação
        colaboradores = colaboradores.filter(
                cpf__icontains=pesquisa
            ) | colaboradores.filter(
                cpf__icontains=cpf_pesquisa
            ) | colaboradores.filter(
                login__icontains=pesquisa
            )

    return render(request, "colaboradores/visualizar.html", {"colaboradores": colaboradores, 'sucesso_cadastro': sucesso_cadastro})

@login_required(login_url='login')   
def Ativar(request, colaborador_id):   # Função para ativar um colaborador, setando o .ativo como True
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    colaborador.ativo = True
    colaborador.save()
    return redirect('visualizar_colaboradores')

@login_required(login_url='login')   
def Inativar(request, colaborador_id): # Função para inativar um colaborador, setando o .ativo como False
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)
    colaborador.ativo = False
    colaborador.save()
    return redirect('visualizar_colaboradores')

@login_required(login_url='login')     
def Alterar(request, colaborador_id):    # Função após o "Salvar" na função Acessar
    colaborador = get_object_or_404(Colaborador, id=colaborador_id)  
    if request.method == "POST":
        colaborador.nome  = request.POST['nome']
        colaborador_cpf  = request.POST['cpf']
        colaborador_cpf = colaborador_cpf.replace('.', '').replace('-', '')
        nome_espaco = colaborador.nome.strip()
        colaborador_id = colaborador.id

        if nome_espaco == '':                   # Verifica se o nome tem apenas espaço
            messages.error(request, 'Insira um nome válido.', extra_tags='erro_nome')
            url = reverse('acessar_colaborador', args=[colaborador_id])
            url += f'?colaborador={colaborador}'
            return redirect(url)

        if not Valida_cpf(colaborador_cpf):    # Verifica a formatação do CPF
            messages.error(request, 'Insira um CPF válido.', extra_tags='erro_cpf')
            url = reverse('acessar_colaborador', args=[colaborador_id])
            url += f'?colaborador={colaborador_id}'
            return redirect(url)
        colaborador.cpf = colaborador_cpf
        colaborador.login  = request.POST['login']
        colaborador_login = Colaborador.objects.filter(login=colaborador.login).exclude(id=colaborador_id)  # Verifica os Logins, menos o próprio da edição
        login_espaco = colaborador.login.strip()
        if login_espaco == '':
            messages.error(request, 'Insira um login válido.', extra_tags='erro_login')
            url = reverse('acessar_colaborador', args=[colaborador_id])
            url += f'?colaborador={colaborador_id}'
            return redirect(url)
        if colaborador_login.exists():
            messages.error(request, 'Login já cadastrado.', extra_tags='erro_login')
            url = reverse('acessar_colaborador', args=[colaborador_id])
            url += f'?colaborador={colaborador_id}'
            return redirect(url)

        colaborador_cpf = Colaborador.objects.filter(cpf=colaborador.cpf).exclude(id=colaborador_id)  # Verifica os CPFs, menos o próprio da edição

        if colaborador_cpf.exists():     # Verifica se o CPF digitado já existe
            return render(request, "colaboradores/acessar.html", {"erro_cpf": "CPF já cadastrado.", "colaborador": colaborador, "campo_foco": "cpf"})
        else:
            try:
                colaborador.save()
                redirect_url = reverse('visualizar_colaboradores') + '?sucesso_cadastro=Colaborador editado com sucesso!'
                return redirect(redirect_url)
            except:
                return render(request, "colaboradores/acessar.html", {"erro": "Erro de edição"})
    else:
        return render(request, "colaboradores/acessar.html", {"colaborador": colaborador})
 
@login_required(login_url='login')    
def Acessar(request, colaborador_id):    # Visualização de edição
    colaborador = Colaborador.objects.get(id=colaborador_id)
    return render(request, 'colaboradores/acessar.html',{'colaborador': colaborador})

def Valida_cpf(cpf):
    cpf = str(cpf)
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    if len(set(cpf)) == 1:                                          # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))            # Calcula o primeiro dígito verificador
    digito1 = (soma * 10) % 11 if soma % 11 > 1 else 0
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))           # Calcula o segundo dígito verificador
    digito2 = (soma * 10) % 11 if soma % 11 > 1 else 0
    return digito1 == int(cpf[9]) and digito2 == int(cpf[10])       # Verifica se os dígitos calculados são iguais aos dígitos do CPF