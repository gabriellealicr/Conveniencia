from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from .models import Produto, Compra, Item_Compra, Colaborador
from datetime import datetime, timedelta
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO
from reportlab.lib.pagesizes import letter
from django.db.models import Sum
from reportlab.lib import colors
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail, EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def Adicionar_produto(request):
    if request.method == 'POST':
        codigo_barras = request.POST.get('codigo_barras')
        produto_codigo_barras = Produto.objects.filter(codigo_barras=codigo_barras)
        if not produto_codigo_barras:    # Verifica se o produto existe
            erro = 'Código de barras inválido!'
            produtos_adicionados = request.session.get('produtos', [])
            valor_total = request.session.get('valor_total', 0)
            return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'valor_total': valor_total, 'erro': erro})

        produto = get_object_or_404(Produto, codigo_barras=codigo_barras)

        if 'produtos' not in request.session:   # Cria a instância da compra se ainda não existir na sessão
            request.session['produtos'] = []
            request.session['valor_total'] = 0
            request.session['itens'] = 0

        produtos = request.session['produtos'] # Verifica se o produto já foi adicionado anteriormente
        produto_existente = None
        for produto_data in produtos:
            if str(produto_data['codigo_barras']) == str(codigo_barras):
                produto_existente = produto_data
                break

        if produto_existente:
            produto_existente['quantidade'] += 1  # Incrementa a quantidade do produto existente
            produto_existente['preco_total'] = produto_existente['preco'] * produto_existente['quantidade']
        else:                                 # Caso o produto ainda não tenha sido adicionado, cria um novo registro na lista de produtos
            contador = len(produtos) + 1      # Atribui um identificador único
            produto_data = {
                'id': contador,
                'nome': produto.nome,
                'codigo_barras': produto.codigo_barras,
                'preco': produto.preco,
                'quantidade': 1,
                'preco_total': produto.preco
            }
            produtos.append(produto_data)

        valor_total = request.session['valor_total']     # Atualiza o valor total da compra na sessão
        valor_total += produto.preco
        request.session['valor_total'] = valor_total

        itens = request.session['itens']
        itens += 1
        request.session['itens'] = itens

        return redirect('conveniencia')

    produtos_adicionados = request.session.get('produtos', [])  # Obtém a lista de produtos adicionados na sessão
    valor_total = request.session.get('valor_total', 0)  # Obtém o valor total da compra na sessão
    itens = request.session.get('itens', 0)
    return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'valor_total': valor_total, 'itens': itens})  # Renderiza a página com os produtos adicionados e o valor total

def calcular_gastos_referencia(colaborador):
    hoje = datetime.now().date()
    mes_passado = (hoje.month - 1) % 12 + 1
    mes_atual = (hoje.month) % 12 + 1
    ano = hoje.year

    # Calcula as datas de referência
    referencia_anterior_inicio = datetime(ano, mes_passado - 2, 26)
    referencia_anterior_fim = datetime(ano if mes_passado != 12 else ano - 1, mes_passado -1, 25)
    referencia_atual_inicio = datetime(ano, mes_passado -1, 26)
    referencia_atual_fim = datetime(ano if mes_atual != 12 else ano - 1, mes_atual -1, 25)

    # Consulta o histórico de compras do colaborador na referência anterior
    compras_referencia_anterior = Compra.objects.filter(
        colaborador=colaborador,
        data__range=[referencia_anterior_inicio, referencia_anterior_fim]
    )
    total_gasto_referencia_anterior = sum(compra.valor_total for compra in compras_referencia_anterior)

    # Consulta o histórico de compras do colaborador na referência atual
    compras_referencia_atual = Compra.objects.filter(
        colaborador=colaborador,
        data__range=[referencia_atual_inicio, referencia_atual_fim]
    )
    print([referencia_atual_inicio, referencia_atual_fim])
    total_gasto_referencia_atual = sum(compra.valor_total for compra in compras_referencia_atual)
    return total_gasto_referencia_anterior, total_gasto_referencia_atual

def Finalizar_compra(request):
    if request.method == 'POST':
        produtos_adicionados = request.session.get('produtos', [])
        valor_total = request.session.get('valor_total', 0)
        quantidade = request.session.get('quantidade', 0)
        login = request.POST['login']
        senha = request.POST['senha']
        colaborador = Colaborador.objects.filter(login=login).first()
        if colaborador:
            if colaborador.ativo:
                if check_password(senha, colaborador.senha):
                    if valor_total > 0:

                        # Cria a nova compra e adiciona os produtos
                        compra = Compra.objects.create(data=datetime.now(), valor_total=valor_total, colaborador=colaborador)
                        for produto_data in produtos_adicionados:
                            produto = get_object_or_404(Produto, codigo_barras=produto_data['codigo_barras'])
                            quantidade = produto_data['quantidade']
                            preco = produto.preco
                            item_compra = Item_Compra.objects.create(compra=compra, produto=produto, preco=preco, quantidade=quantidade)
                            compra.produtos.add(produto)  # Adiciona o produto à relação ManyToMany
                        request.session['produtos'] = []  # Limpa a lista de produtos na sessão
                        request.session['valor_total'] = 0  # Reseta o valor total da compra na sessão
                        request.session['itens'] = 0  # Reseta os itens na sessão

                        # Salva a instância de Compra antes de chamar o método referencia
                        compra.save()
                                             # Cria um objeto PDF
                        response = HttpResponse(content_type='application/pdf')
                        response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'

                        # Generate the content of the PDF report
                        p = canvas.Canvas(response, pagesize=letter)
                        # Your code to create the content of the report...

                        # Finalize the PDF document
                        p.showPage()
                        p.save()

                        # Create the email
                        subject = 'Conveniência 2.0 - Relatório de consumo geral'
                        message = 'A sua compra foi finalizada com sucesso!'
                        from_email = 'testeacademia@sci.com.br'
                        to_email = 'gabriellealicr@gmail.com'

                        # Render the email template
                        email_template = 'compra/rel.html'  # Replace with the name of your template
                        email_context = {
                            'subject': subject,
                            'message': message,
                        }
                        email_html = render_to_string(email_template, email_context)

                        # Send the email with the attachment
                        email = EmailMessage(subject, email_html, from_email, [to_email])
                        email.attach('relatorio.pdf', response.getvalue(), 'application/pdf')
                        email.send()

                        # subject = 'Conveniência 2.0.'
                        # message = 'A sua compra foi finalizada com sucesso!'
                        # from_email = 'testeacademia@sci.com.br'
                        # to_email = 'gabriellealicr@gmail.com' 
                        # send_mail(subject, message, from_email, [to_email])

                        # Calcula os gastos de referência
                        total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(colaborador)
                        return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior,'gasto_referencia_atual': total_gasto_referencia_atual,'colaborador':colaborador}) 
                    total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(colaborador)
                    return render(request, 'compra/conveniencia.html', {'mostrar_ref': True,'gasto_referencia_anterior': total_gasto_referencia_anterior,'gasto_referencia_atual': total_gasto_referencia_atual,'colaborador': colaborador})  
                return render(request, 'compra/conveniencia.html', {'erro_senha': 'Senha incorreta!','produtos_adicionados': produtos_adicionados,'valor_total': valor_total})
            return render(request, 'compra/conveniencia.html', {'erro_inativo': 'Colaborador está inativo!','produtos_adicionados': produtos_adicionados,'valor_total': valor_total})
        return render(request, 'compra/conveniencia.html', {'erro_colab': 'Colaborador não cadastrado!','produtos_adicionados': produtos_adicionados,'valor_total': valor_total})
    return redirect('conveniencia')


def Verificar_referencia(request):
    if request.method == 'POST':
        login = request.POST['login']
        senha = request.POST['senha']
        colaborador = Colaborador.objects.filter(login=login).first()

        produtos_adicionados = request.session.get('produtos', [])
        valor_total = request.session.get('valor_total', 0)
        itens = request.session.get('itens', 0)
        if colaborador:
            if colaborador.ativo:
                if check_password(senha, colaborador.senha):
                    total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(colaborador)
                    return render(request, 'compra/conveniencia.html', {'mostrar_ref': True,'gasto_referencia_anterior': total_gasto_referencia_anterior,'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total})  
                return render(request, 'compra/conveniencia.html', {'erro_senha': 'Senha incorreta!'})
            return render(request, 'compra/conveniencia.html', {'erro_inativo': 'Colaborador está inativo!'})
        return render(request, 'compra/conveniencia.html', {'erro_colab': 'Colaborador não cadastrado!'})
    return redirect('conveniencia')

@login_required(login_url='login')
def Historico(request):
    compras = Compra.objects.all()
    pesquisa = request.GET.get('pesquisa')
    if pesquisa:
        try: # Verifica se o valor de pesquisa é uma data válida nos formatos desejados
            data_pesquisa = datetime.strptime(pesquisa, "%d-%m-%Y")  # Converte para o formato "dd-mm-yyyy"
        except ValueError:
            try:
                data_pesquisa = datetime.strptime(pesquisa, "%d/%m/%Y")  # Converte para o formato "dd/mm/yyyy"
            except ValueError:
                data_pesquisa = None
        if data_pesquisa:           # Filtra as compras pela data de compra
            compras = compras.filter(data__date=data_pesquisa)
        else:
            compras = []
    return render(request, 'compra/historico.html', {'compras': compras})

def Limpar(request):
    if 'compra_id' in request.session:
        del request.session['compra_id']
    if 'produtos' in request.session:
        del request.session['produtos']
    if 'valor_total' in request.session:
        del request.session['valor_total']
    return redirect('conveniencia')  

def Excluir_produto(request, produto_id):
    produtos_adicionados = request.session.get('produtos', [])  # Obtém a lista de produtos adicionados na sessão

    produto_excluido = None
    for produto in produtos_adicionados:
        if produto['id'] == produto_id:      # Encontra o produto com base no identificador único
            produto_excluido = produto
            break

    if produto_excluido:                     # Se o produto for encontrado, remove da lista e atualiza o valor total
        produtos_adicionados.remove(produto_excluido)
        valor_total = request.session.get('valor_total', 0)  # Obtém o valor total da compra na sessão
        valor_total -= produto_excluido['preco']
        request.session['valor_total'] = valor_total
        itens = request.session['itens']                     # Obtém a qtd de itens da compra na sessão
        itens -= 1
        request.session['itens'] = itens

    return redirect('conveniencia')  

def Relatorio_consumo(request):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        colaborador_pesquisa = request.POST.get('colaborador_pesquisa')
        colaborador_pesquisa = Colaborador.objects.filter(login=colaborador_pesquisa).first()

        # Converta as datas de string para objetos datetime
        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
        if data_fim:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()

        # Filtra as compras com base nas datas e colaborador pesquisados
        compras = Compra.objects.all()
        if data_inicio and data_fim:
            compras = compras.filter(data__range=[data_inicio, data_fim])
        if colaborador_pesquisa:
            compras = compras.filter(colaborador__nome__icontains=colaborador_pesquisa)
        else:
            messages.error(request, 'Colaborador não encontrado!', extra_tags='colab_nao_encontrado')
            url = reverse('relatorio_consumo')
            return redirect(url)

        # Gere o relatório em PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio_consumo.pdf"'
        p = canvas.Canvas(response)

        # Cabeçalho do relatório
        cor = colors.HexColor("#00008B")
        p.setFillColor(cor)
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(300, 750, "Relatório de consumo geral")
        p.setFillColor(colors.black)

        # Dados de consumo por colaborador
        p.setFont("Helvetica", 12)
        y = 700
        for compra in compras:
            colaborador = compra.colaborador
            valor_total = compra.valor_total
            data = compra.data.strftime("%d-%m-%Y")
            p.drawString(50, y, f"Colaborador: {colaborador.nome}")
            p.drawString(50, y - 20, f"Data da compra: {data}")
            p.drawString(50, y - 40, f"Valor total: R${valor_total}")
            y -= 60

        p.showPage()
        p.save()

        return response
    colaborador = Colaborador.objects.all()
    return render(request, 'relatorios/relatorio_consumo.html',{'colaboradores': colaborador})

def Relatorio_geral(request):
    if request.method == 'POST':
        hoje = datetime.now().date()
        mes_passado = (hoje.month - 1) % 12 + 1
        mes_atual = (hoje.month) % 12 + 1
        ano = hoje.year

        # Calcula as datas de referência
        referencia_anterior_inicio = datetime(ano, mes_passado - 2, 26)
        referencia_anterior_fim = datetime(ano if mes_passado != 12 else ano - 1, mes_passado -1, 25)
        referencia_atual_inicio = datetime(ano, mes_passado -1, 26)
        referencia_atual_fim = datetime(ano if mes_atual != 12 else ano - 1, mes_atual -1, 25)

        # Consulta o histórico de compras na referência anterior
        compras_referencia_anterior = Compra.objects.filter(
            data__range=[referencia_anterior_inicio, referencia_anterior_fim]
        )
        total_gasto_referencia_anterior = compras_referencia_anterior.aggregate(Sum('valor_total'))['valor_total__sum'] or 0

        # Consulta o histórico de compras na referência atual
        compras_referencia_atual = Compra.objects.filter(
            data__range=[referencia_atual_inicio, referencia_atual_fim]
        )
        total_gasto_referencia_atual = compras_referencia_atual.aggregate(Sum('valor_total'))['valor_total__sum'] or 0

        # Cria um objeto PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'

        # Cria o conteúdo do relatório em PDF
        p = canvas.Canvas(response, pagesize=letter)
        cor = colors.HexColor("#00008B")
        p.setFillColor(cor)
        p.setFont("Helvetica-Bold", 14)
        p.drawCentredString(300, 750, "Relatório de consumo geral")
        p.setFillColor(colors.black)
        p.setFont("Helvetica", 12)
        p.drawString(100, 700, f"Total gasto na referência atual: R$ {total_gasto_referencia_atual}")
        # Finaliza o documento PDF
        p.showPage()
        p.save()

        return response
    return render(request, 'relatorios/relatorio_geral.html')