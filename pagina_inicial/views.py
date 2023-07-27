from django.shortcuts import render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from colaboradores.models import Colaborador
from produtos.models import Produto
from estoque.models import Estoque
import plotly.graph_objects as go
from django.db.models import Count
from django.views.decorators.cache import never_cache
from datetime import datetime
from compra.models import Compra
from django.db.models import Sum

@never_cache
@login_required(login_url='login')
def Pagina_inicial(request):
    grafico = criar_grafico()
    grafico_produtos = criar_grafico_produtos()
    sucess_login_message = 'Você está logado como Super User!'
    # Verificação para a mensagem aparecer apenas quando logar
    if 'login_message_displayed' not in request.session:
        user = request.user
        if user.is_superuser:
            sucess_login_message = 'Você está logado como Super User!'
        else:
            sucess_login_message = 'Você está logado como Usuário Comum!'
        request.session['login_message_displayed'] = True
        messages.success(request, sucess_login_message,
                         extra_tags='sucess_login_message')
        url = reverse('pagina_inicial')
        url += f'?sucess_login_message={sucess_login_message}'
        return redirect(url)
    produtos_baixo_estoque = obter_produtos_baixo_estoque().order_by('quantidade')
    referencia_anterior, referencia_atual = referencia()
    referencia_anterior = f"{referencia_anterior:.2f}".replace(
                        '.', ',')
    referencia_atual = f"{referencia_atual:.2f}".replace(
                        '.', ',')
    return render(request, 'pagina_inicial/pagina_inicial.html', {'grafico': grafico, 'grafico_produtos': grafico_produtos, 'produtos_baixo_estoque': produtos_baixo_estoque, 'referencia_anterior': referencia_anterior, 'referencia_atual': referencia_atual})

def obter_produtos_baixo_estoque():
    return Estoque.objects.filter(quantidade__lt=4)

# Funções para contar registros de colaboradores, produtos e usuários, e apresentar no dashboard - página inicial

def obter_contagem_colaboradores():
    return Colaborador.objects.count()


def obter_contagem_produtos():
    return Produto.objects.count()


def obter_contagem_usuarios():
    return User.objects.count()

def referencia():
    hoje = datetime.now().date()
    mes_passado = (hoje.month - 1) % 12 + 1
    mes_atual = (hoje.month) % 12 + 1
    ano = hoje.year

    referencia_anterior_inicio = datetime(ano, mes_passado - 1, 26, 00, 00)
    referencia_anterior_fim = datetime(
        ano if mes_passado != 12 else ano - 1, mes_passado, 25, 23, 59)
    referencia_atual_inicio = datetime(ano, mes_passado, 26, 00, 00)
    referencia_atual_fim = datetime(
        ano if mes_atual != 12 else ano - 1, mes_atual, 25, 23, 59)

    # Consulta o histórico de compras na referência anterior
    compras_referencia_anterior = Compra.objects.filter(
        data__range=[referencia_anterior_inicio, referencia_anterior_fim]
    )
    total_gasto_referencia_anterior = compras_referencia_anterior.aggregate(
        Sum('valor_total'))['valor_total__sum'] or 0

    # Consulta o histórico de compras na referência atual
    compras_referencia_atual = Compra.objects.filter(
        data__range=[referencia_atual_inicio, referencia_atual_fim]
    )
    total_gasto_referencia_atual = compras_referencia_atual.aggregate(
        Sum('valor_total'))['valor_total__sum'] or 0
    
    return total_gasto_referencia_anterior, total_gasto_referencia_atual



def criar_grafico():       # Gráfico de apresentação de quantidade
    labels = ['Colaboradores', 'Produtos', 'Usuários']
    contagens = [obter_contagem_colaboradores(
    ), obter_contagem_produtos(), obter_contagem_usuarios()]

    # Biblioteca do gráfico
    fig = go.Figure(data=[go.Bar(x=labels, y=contagens)])
    fig.update_layout(xaxis_title='Categoria',
                      plot_bgcolor='#f1f9ff',
                      paper_bgcolor='#f1f9ff',
                      font_color='black',
                      )

    return fig.to_html(full_html=False)


def obter_produtos_mais_vendidos():
    return Produto.objects.annotate(total_vendido=Count('compra__item_compra')).order_by('-total_vendido')[:5]


def criar_grafico_produtos():
    produtos_mais_vendidos = obter_produtos_mais_vendidos()
    labels = [produto.nome for produto in produtos_mais_vendidos]
    contagens = [produto.total_vendido for produto in produtos_mais_vendidos]

    fig = go.Figure(data=[go.Bar(x=labels, y=contagens)])

    # Atualize o layout do gráfico
    fig.update_layout(
        xaxis_title='Produto',
        yaxis_title='Quantidade',
        plot_bgcolor='#f1f9ff',
        paper_bgcolor='#f1f9ff',
        font_color='black'
    )

    return fig.to_html(full_html=False)
