from django.shortcuts import render, reverse, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from colaboradores.models import Colaborador
from produtos.models import Produto
import plotly.graph_objects as go
from django.db.models import Count


@login_required(login_url='login')    
def Pagina_inicial(request):
    grafico = criar_grafico()
    grafico_produtos = criar_grafico_produtos()
    sucess_login_message = 'Você está logado como Super User!' 
    if 'login_message_displayed' not in request.session:     # Verificação para a mensagem aparecer apenas quando logar
        user = request.user
        if user.is_superuser:
            sucess_login_message = 'Você está logado como Super User!'
        else:
            sucess_login_message = 'Você está logado como Usuário Comum!'
        request.session['login_message_displayed'] = True
        messages.success(request, sucess_login_message, extra_tags='sucess_login_message')
        url = reverse('pagina_inicial')
        url += f'?sucess_login_message={sucess_login_message}'
        return redirect(url)
        # return render(request, 'pagina_inicial/pagina_inicial.html', {'sucess_login_message': sucess_login_message, 'grafico': grafico, 'grafico_produtos': grafico_produtos})
    return render(request, 'pagina_inicial/pagina_inicial.html',{'grafico': grafico, 'grafico_produtos': grafico_produtos})

# Funções para contar registros de colaboradores, produtos e usuários, e apresentar no dashboard - página inicial

def obter_contagem_colaboradores():
    return Colaborador.objects.count()

def obter_contagem_produtos():
    return Produto.objects.count()

def obter_contagem_usuarios():
    return User.objects.count()

def criar_grafico():       # Gráfico de apresentação de quantidade
    labels = ['Colaboradores', 'Produtos', 'Usuários']
    contagens = [obter_contagem_colaboradores(), obter_contagem_produtos(), obter_contagem_usuarios()]

    fig = go.Figure(data=[go.Bar(x=labels, y=contagens)])  # Biblioteca do gráfico
    fig.update_layout(xaxis_title='Categoria',   
                    plot_bgcolor='#f1f9ff',  
                    paper_bgcolor='#f1f9ff', 
                    font_color='black'
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
        plot_bgcolor='#f1f9ff',  
        paper_bgcolor='#f1f9ff',  
        font_color='black'  
    )

    return fig.to_html(full_html=False)

