from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from . models import Produto
from django.core.exceptions import ValidationError
import logging 
logger = logging.getLogger()
from django.contrib import messages

@login_required(login_url='login')    
def Cadastro(request):
    if request.method == "POST":        # Quando o método é POST, ou seja, ao clicar no botão "Salvar", que é um submit
        nome_produto = request.POST.get('nome')
        codigo_barras_produto = request.POST.get('codigo_barras')
        
        preco_produto = request.POST.get('preco')
        preco_produto = preco_produto.replace('R$', '').replace('\xa0', '').replace(',', '.')  # Remove o símbolo "R$" 
        
        nome_espaco = nome_produto.strip()

        if nome_espaco == '':     # Verifica se o nome é apenas espaço
            messages.error(request, 'Insira um nome válido.', extra_tags='erro_nome')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        
        if len(codigo_barras_produto) != 13:        # Verifica se o código de barras contém 13 números
            messages.error(request, 'Código de barras deve conter 13 números.', extra_tags='erro_codigo_barras')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        produto_codigo_barras = Produto.objects.filter(codigo_barras=codigo_barras_produto).first()  # Busca o código de barras digitado
        if produto_codigo_barras:                   # Caso já exista o código de barras
            messages.error(request, 'Código de barras já cadastrado.', extra_tags='erro_codigo_barras_cad')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        if preco_produto=='0.00':
            messages.error(request, 'Insira um preço válido.', extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        print(preco_produto)
        try:
            preco_produto = float(preco_produto)  # Converter para float
        except ValueError:
            messages.error(request, 'Insira um preço válido.', extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        produto = Produto(nome=nome_produto, codigo_barras=codigo_barras_produto, preco=preco_produto) 
        try:
            produto.save()
            url = reverse('visualizar_produtos') 
            url += f'?sucesso_cadastro=Produto cadastrado com sucesso!'
            return redirect(url)
        except ValidationError:
            messages.error(request, 'Erro de cadastro.', extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)    # Caso ocorra erro de sistema
    
    else:     # Quando o método não é POST, ou seja, entrando no formulário para cadastrar
        return render(request, "produtos/cadastro.html", {"campo_foco": "nome"})

@login_required(login_url='login')    
def Visualizar(request):
    sucesso_cadastro = request.GET.get('sucesso_cadastro')
    try:
        produto = Produto.objects.all()        # Lista todos os produtos cadastrados
        pesquisa = request.GET.get('pesquisa')
        if pesquisa:
            print(request.GET.get('pesquisa')) # Filtro de pesquisa, onde o icontains busca pelo input de pesquisa e ignora up e low case
            produto = produto.filter(
                nome__icontains=pesquisa
            ) | produto.filter(
                codigo_barras__icontains=pesquisa
            )
        return render(request, "produtos/visualizar.html", {"produtos": produto, "sucesso_cadastro": sucesso_cadastro})   # Retorna a pesquisa
    except Exception as e:
        logger.exception(e)
        return render(request, "pagina_inicial/pagina_inicial.html", {"erro": str(e)}) # Caso ocorra erro de sistema
    
@login_required(login_url='login')   
def Ativar(request, produto_id):   # Função para ativar um colaborador, setando o .ativo como True
    produto = get_object_or_404(Produto, id=produto_id)
    produto.ativo = True
    produto.save()
    return redirect('visualizar_produtos')

@login_required(login_url='login')   
def Inativar(request, produto_id): # Função para inativar um colaborador, setando o .ativo como False
    produto = get_object_or_404(Produto, id=produto_id)
    produto.ativo = False
    produto.save()
    return redirect('visualizar_produtos')
    
@login_required(login_url='login')     
def Alterar(request, produto_id):   # Função após o "Salvar" na função Acessar
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == "POST":
        id = request.POST['produto_id']
        produto.nome = request.POST['nome']
        codigo_barras_produto = request.POST['codigo_barras']
        preco = request.POST['preco']
        preco = preco.replace('R$', '').replace('\xa0', '').replace(',', '.')  # Remove o símbolo "R$" 
        nome_espaco = produto.nome.strip()

        produto_codigo_barras = Produto.objects.filter(codigo_barras=codigo_barras_produto).exclude(id=id)
        if produto_codigo_barras.exists():                           # Verifica se o código de barras já está cadastrado
            messages.error(request, 'Código de barras já cadastrado.', extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            produto.codigo_barras = int(codigo_barras_produto)       # Verifica se o código de barras contém apenas números
        except ValueError:
            messages.error(request, 'Código de barras deve conter apenas números.', extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        if nome_espaco == '':                                # Verifica se o nome do produto contém apenas espaços
            messages.error(request, 'Insira um nome válido.', extra_tags='erro_nome')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        if len(str(produto.codigo_barras)) != 13:            # Verifica se o código de barras possui 13 números
            messages.error(request, 'Código de barras deve conter 13 números.', extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        if preco=='0.00':
            messages.error(request, 'Insira um preço válido.', extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            produto.preco = float(preco)                     # Verifica se o preço é um número válido
        except ValueError:
            messages.error(request, 'Insira um preço válido.', extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            produto.save()
            url = reverse('visualizar_produtos') 
            url += f'?sucesso_cadastro=Produto editado com sucesso!'
            return redirect(url)
        except:
            messages.error(request, 'Erro de edição.', extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
    else:
        return render(request, "produtos/acessar.html", {"produto": produto})

@login_required(login_url='login')    
def Acessar(request, produto_id):    # Visualização de edição
    produto = Produto.objects.get(id=produto_id)
    return render(request, 'produtos/acessar.html',{'produto': produto})