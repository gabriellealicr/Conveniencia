from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib.auth.decorators import login_required
from . models import Produto
from estoque.models import Estoque
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger()
from django.views.decorators.cache import never_cache


@never_cache
@login_required(login_url='login')
def Cadastro(request):
    if request.method == "POST":        # Quando o método é POST, ou seja, ao clicar no botão "Salvar", que é um submit
        nome_produto = request.POST.get('nome')
        codigo_barras_produto = request.POST.get('codigo_barras')
        opc = request.POST.get('opc')
        preco_produto = request.POST.get('preco')
        preco_produto = preco_produto.replace('R$', '').replace(
            '\xa0', '').replace(',', '.')  # Remove o símbolo "R$"

        nome_espaco = nome_produto.strip()

        if nome_espaco == '':     # Verifica se o nome é apenas espaço
            messages.error(request, 'Insira um nome válido.',
                           extra_tags='erro_nome')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)

        # Verifica se o código de barras contém 13 números
        if len(codigo_barras_produto) != 13:
            messages.error(
                request, 'Código deve conter 13 números.', extra_tags='erro_codigo_barras')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        produto_codigo_barras = Produto.objects.filter(
            codigo_barras=codigo_barras_produto).first()  # Busca o código de barras digitado
        if produto_codigo_barras:                   # Caso já exista o código de barras
            messages.error(request, 'Código de barras já cadastrado.',
                           extra_tags='erro_codigo_barras_cad')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        if preco_produto == '0.00':
            messages.error(request, 'Insira um preço válido.',
                           extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        try:
            preco_produto = float(preco_produto)  # Converter para float
        except ValueError:
            messages.error(request, 'Insira um preço válido.',
                           extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)
        if opc == '1': opc = 'Alimento'
        if opc == '2': opc = 'Bebida'
        if opc == '3': opc = 'Camiseta'
        if opc == '4': opc = 'Ingresso'
        produto = Produto(
            nome=nome_produto, codigo_barras=codigo_barras_produto, preco=preco_produto, tipo=opc)
        try:
            produto.save()
            estoque = Estoque(produtos=produto)
            estoque.save()
            url = reverse('visualizar_produtos')
            messages.success(request,f'Produto {produto.nome} cadastrado com sucesso!', extra_tags='sucesso_cadastro')
            return redirect(url)
        except ValidationError:
            messages.error(request, 'Erro de cadastro.',
                           extra_tags='erro_preco')
            url = reverse('cadastro_produto')
            url += f'?nome={nome_produto}&codigo_barras={codigo_barras_produto}&preco={preco_produto}'
            return redirect(url)    # Caso ocorra erro de sistema

    else:     # Quando o método não é POST, ou seja, entrando no formulário para cadastrar
        return render(request, "produtos/cadastro.html")


@never_cache
@login_required(login_url='login')
def Visualizar(request):
    sucesso_cadastro = request.GET.get('sucesso_cadastro')
    produto = Produto.objects.all().order_by('-ativo', 'nome')

    return render(request, "produtos/visualizar.html", {"produtos": produto, "sucesso_cadastro": sucesso_cadastro})


@never_cache
@login_required(login_url='login')
def Ativar(request, produto_id):   # Função para ativar um colaborador, setando o .ativo como True
    produto = get_object_or_404(Produto, id=produto_id)
    produto.ativo = True
    produto.save()
    url = reverse('visualizar_produtos')
    messages.success(request,f'Produto {produto.nome} ativado com sucesso!', extra_tags='sucesso_cadastro')
    return redirect(url)


@never_cache
@login_required(login_url='login')
# Função para inativar um colaborador, setando o .ativo como False
def Inativar(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    produto.ativo = False
    produto.save()
    url = reverse('visualizar_produtos')
    messages.success(request,f'Produto {produto.nome} inativado com sucesso!', extra_tags='sucesso_cadastro')
    return redirect(url)


@never_cache
@login_required(login_url='login')
def Alterar(request, produto_id):   # Função após o "Salvar" na função Acessar
    produto = get_object_or_404(Produto, id=produto_id)
    if request.method == "POST":
        id = request.POST['produto_id']
        produto.nome = request.POST['nome']
        codigo_barras_produto = request.POST['codigo_barras']
        preco = request.POST['preco']
        preco = preco.replace('R$', '').replace(
            '\xa0', '').replace(',', '.')  # Remove o símbolo "R$"
        nome_espaco = produto.nome.strip()
        opc = request.POST.get('opc')

        produto_codigo_barras = Produto.objects.filter(
            codigo_barras=codigo_barras_produto).exclude(id=id)
        # Verifica se o código de barras já está cadastrado
        if produto_codigo_barras.exists():
            messages.error(request, 'Código de barras já cadastrado.',
                           extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            # Verifica se o código de barras contém apenas números
            produto.codigo_barras = int(codigo_barras_produto)
        except ValueError:
            messages.error(
                request, 'Código deve conter apenas números.', extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        if nome_espaco == '':                                # Verifica se o nome do produto contém apenas espaços
            messages.error(request, 'Insira um nome válido.',
                           extra_tags='erro_nome')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        # Verifica se o código de barras possui 13 números
        if len(str(produto.codigo_barras)) != 13:
            messages.error(
                request, 'Código deve conter 13 números.', extra_tags='erro_codigo_barras')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        if preco == '0.00':
            messages.error(request, 'Insira um preço válido.',
                           extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            # Verifica se o preço é um número válido
            produto.preco = float(preco)
        except ValueError:
            messages.error(request, 'Insira um preço válido.',
                           extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
        try:
            if opc == '1': opc = 'Alimento'
            if opc == '2': opc = 'Bebida'
            if opc == '3': opc = 'Camiseta'
            if opc == '4': opc = 'Ingresso'
            produto.tipo = opc
            produto.save()
            url = reverse('visualizar_produtos')
            messages.success(request,f'Produto {produto.nome} alterado com sucesso!', extra_tags='sucesso_cadastro')
            return redirect(url)
        except:
            messages.error(request, 'Erro de edição.', extra_tags='erro_preco')
            url = reverse('acessar_produto', args=[produto_id])
            url += f'?produto={produto}'
            return redirect(url)
    else:
        return render(request, "produtos/acessar.html", {"produto": produto})


@never_cache
@login_required(login_url='login')
def Acessar(request, produto_id):    # Visualização de edição
    produto = Produto.objects.get(id=produto_id)
    return render(request, 'produtos/acessar.html', {'produto': produto})
