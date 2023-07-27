from django.shortcuts import render, redirect, reverse, get_object_or_404
from produtos.models import Produto
from django.contrib.auth.decorators import login_required
import logging
logger = logging.getLogger()
from django.views.decorators.cache import never_cache
from .models import Estoque, MovimentacaoEstoque
from datetime import datetime
from django.contrib import messages
from django.db.models import F

@never_cache
@login_required(login_url='login')
def Visualizar(request):  
    produto = Produto.objects.all()
    estoque = Estoque.objects.all()
    sucesso_cadastro = request.GET.get('sucesso_cadastro')

    return render(request, "estoque/visualizar.html", {"produtos": produto, 'estoque': estoque, 'sucesso_cadastro': sucesso_cadastro})

@login_required(login_url='login')
def Att_qtd_entrada(request, estoque_id):
    if request.method == 'POST':
        entrada = request.POST.get('entrada')
        estoque = get_object_or_404(Estoque, id=estoque_id)
        estoque.quantidade = estoque.quantidade + int(entrada)
        estoque.save()

        movimentacao = MovimentacaoEstoque()
        movimentacao.estoque = estoque
        movimentacao.data_hora = datetime.now()
        movimentacao.usuario = request.user
        movimentacao.quantidade_alteracao = int(entrada)
        movimentacao.tipo = 'Entrada'
        movimentacao.save()
        url = reverse('estoque')
        messages.success(request,f'Estoque de produto {estoque.produtos.nome} alterado com sucesso!', extra_tags='sucesso_cadastro')
        return redirect(url)

    return redirect('estoque')

@login_required(login_url='login')
def Att_qtd_saida(request, estoque_id):
    if request.method == 'POST':
        saida = request.POST.get('saida')
        estoque = get_object_or_404(Estoque, id=estoque_id)
        if int(saida) > estoque.quantidade:
            messages.error(request, 'Não é possível realizar a movimentação!',
                               extra_tags='erro')
            url = reverse('saida_estoque', args=[estoque_id])
            return redirect(url)
        
        estoque.quantidade = estoque.quantidade - int(saida)
        estoque.save()

        movimentacao = MovimentacaoEstoque()
        movimentacao.estoque = estoque
        movimentacao.data_hora = datetime.now()
        movimentacao.usuario = request.user
        movimentacao.quantidade_alteracao = int(saida)
        movimentacao.tipo = 'Saída'
        movimentacao.save()
        url = reverse('estoque')
        messages.success(request,f'Estoque de produto {estoque.produtos.nome} alterado com sucesso!', extra_tags='sucesso_cadastro')
        return redirect(url)

    return redirect('estoque')


@never_cache
@login_required(login_url='login')
def Acessar(request, produto_id):    # Visualização de edição
    produto = Produto.objects.get(id=produto_id)
    return render(request, 'produtos/acessar.html', {'produto': produto})

@never_cache
@login_required(login_url='login')
def Entrada_estoque(request, estoque_id):  
    estoque = Estoque.objects.get(id=estoque_id)

    return render(request, "estoque/entrada_estoque.html", {'estoque': estoque})

@never_cache
@login_required(login_url='login')
def Saida_estoque(request, estoque_id):  
    estoque = Estoque.objects.get(id=estoque_id)

    return render(request, "estoque/saida_estoque.html", {'estoque': estoque})

@never_cache
@login_required(login_url='login')
def Movimentacao(request):  
    produto = Produto.objects.all()
    estoque = Estoque.objects.all()
    movimentacao = MovimentacaoEstoque.objects.all()

    return render(request, "estoque/movimentacao.html", {'estoque': estoque, 'produto': produto, 'movimentacao': movimentacao})