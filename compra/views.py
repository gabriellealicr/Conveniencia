from django import template
import locale
from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib.auth.decorators import login_required
from .models import Produto, Compra, Item_Compra, Colaborador
from estoque.models import Estoque
from django.contrib.auth.models import User
from datetime import datetime
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from django.db.models import Sum, Count
from reportlab.lib import colors
from django.contrib import messages
from django.contrib.auth.hashers import check_password
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import re
from django.db.models import F
from datetime import timedelta, date
from PIL import Image
import cv2 # Lê imagem / entrada de vídeo da câmera
from pyzbar.pyzbar import decode # Biblioteca para decodificar códigos de barras e QR codes

def Add_prod_codigo(request):
    cap = cv2.VideoCapture(0) # Inicializa a captura de vídeo da câmera. O valor 0 indica que será usada a câmera padrão
    cap.set(3, 640) # Define a largura do vídeo 
    cap.set(4, 480) # Define a altura do vídeo
    camera = True
    while camera == True:
        sucess, frame = cap.read() # Captura um quadro (frame) do vídeo da câmera
        cv2.imshow('Testando', frame) # Exibe o frame em uma janela
        cv2.waitKey(1) # Aguarda por 1 milissegundo para que a janela seja atualizada
        if cv2.waitKey(1) & 0xFF == 27:
            cap.release() # Libera o dispositivo de captura (a câmera)
            cv2.destroyAllWindows() # Fecha a janela
            break
        if not sucess:
            cap.release() # Libera o dispositivo de captura (a câmera)
            cv2.destroyAllWindows() # Fecha a janela
        for code in decode(frame): # Decodifica os códigos presentes no frame
            print(code.data.decode('utf-8'))
            codigo = code.data.decode('utf-8') # dado decodificado
            if codigo:
                cap.release() # Libera o dispositivo de captura (a câmera)
                cv2.destroyAllWindows() # Fecha a janela
                produto_codigo_barras = Produto.objects.filter(
                codigo_barras=codigo)
                if not produto_codigo_barras:
                    produtos_adicionados = request.session.get('produtos', [])
                    valor_total = request.session.get('valor_total', 0)
                    messages.error(request, 'Código de barras inválido!',
                                extra_tags='erro_inativo')
                    url = reverse('conveniencia')
                    return redirect(url)
                produto = get_object_or_404(Produto, codigo_barras=codigo)
                if not produto.ativo:
                    messages.error(request, 'Produto está inativo!',
                                extra_tags='erro_inativo')
                    url = reverse('conveniencia')
                    return redirect(url)

                if 'produtos' not in request.session:   # Cria a instância da compra se ainda não existir na sessão
                    request.session['produtos'] = []
                    request.session['valor_total'] = 0
                    request.session['itens'] = 0

                # Verifica se o produto já foi adicionado anteriormente
                produtos = request.session['produtos']
                produto_existente = None
                for produto_data in produtos:
                    if str(produto_data['codigo_barras']) == str(codigo):
                        produto_existente = produto_data
                        break
                estoque = get_object_or_404(Estoque, produtos=produto)
                if estoque.quantidade <= 0:
                    messages.error(request, 'Estoque indisponível!',
                                extra_tags='erro_inativo')
                    url = reverse('conveniencia')
                    return redirect(url)

                if produto_existente:
                    # Incrementa a quantidade do produto existente
                    produto_existente['quantidade'] += 1
                    produto_existente['preco_total'] = produto_existente['preco'] * \
                        produto_existente['quantidade']

                    if estoque.quantidade < produto_existente['quantidade']:
                        messages.error(request, 'Estoque indisponível!',
                                    extra_tags='erro_inativo')
                        url = reverse('conveniencia')
                        return redirect(url)
                else:                                 # Caso o produto ainda não tenha sido adicionado, cria um novo registro na lista de produtos
                    contador = len(produtos) + 1      # Atribui um identificador único
                    preco = f"{produto.preco:.2f}".replace('.', ',')
                    produto_data = {
                        'id': contador,
                        'nome': produto.nome,
                        'codigo_barras': produto.codigo_barras,
                        'preco': preco,
                        'quantidade': 1,
                        'preco_total': produto.preco
                    }
                    produtos.append(produto_data)

                # Atualiza o valor total da compra na sessão
                valor_total = request.session['valor_total']
                valor_total += produto.preco
                request.session['valor_total'] = valor_total

                itens = request.session['itens']
                itens += 1
                request.session['itens'] = itens

                return redirect('conveniencia')

            # Obtém a lista de produtos adicionados na sessão
            produtos_adicionados = request.session.get('produtos', [])
            # Obtém o valor total da compra na sessão
            valor_total = request.session.get('valor_total', 0)
            valor_total = f"{valor_total:.2f}".replace('.', ',')
            itens = request.session.get('itens', 0)
            # Renderiza a página com os produtos adicionados e o valor total
            return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'valor_total': valor_total, 'itens': itens})
    return redirect('conveniencia')

def Finalizar_compra_codigo(request):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    camera = True
    itens = request.session['itens']
    while camera == True:
        sucess, frame = cap.read()
        cv2.imshow('Testando', frame)
        cv2.waitKey(1)
        if cv2.waitKey(1) & 0xFF == 27:
            cap.release() # Libera o dispositivo de captura (a câmera)
            cv2.destroyAllWindows() # Fecha a janela
            break
        for code in decode(frame):
            codigo = code.data.decode('utf-8')
            if codigo:
                cap.release()
                cv2.destroyAllWindows()
                produtos_adicionados = request.session.get('produtos', [])
                if produtos_adicionados == []:
                    messages.error(request, 'Carrinho vazio! Por favor, adicione um produto para realizar a compra',
                            extra_tags='erro_inativo')
                    url = reverse('conveniencia')
                    return redirect(url)
                valor_total = request.session.get('valor_total', 0)
                valor_total = float(valor_total)
                quantidade = request.session.get('quantidade', 0)
                colaborador = Colaborador.objects.filter(codigo=codigo).first()
                if colaborador:
                    if colaborador.ativo:
                        if colaborador.ativo:
                            if valor_total > 0:

                                # Cria a nova compra e adiciona os produtos
                                compra = Compra.objects.create(
                                    data=datetime.now(), valor_total=valor_total, colaborador=colaborador)
                                data = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                                for produto_data in produtos_adicionados:
                                    produto = get_object_or_404(
                                        Produto, codigo_barras=produto_data['codigo_barras'])
                                    quantidade = produto_data['quantidade']
                                    preco = produto.preco
                                    item_compra = Item_Compra.objects.create(
                                        compra=compra, produto=produto, preco=preco, quantidade=quantidade)
                                    # Adiciona o produto à relação ManyToMany
                                    compra.produtos.add(produto)
                                # Limpa a lista de produtos na sessão
                                request.session['produtos'] = []
                                # Reseta o valor total da compra na sessão
                                request.session['valor_total'] = 0
                                # Reseta os itens na sessão
                                request.session['itens'] = 0
                                # Atualiza a quantidade no estoque
                                if not produto.tipo == 'Ingresso' and not produto.tipo == 'Camiseta':
                                    estoque = Estoque.objects.get(produtos=produto)
                                    estoque.quantidade = F('quantidade') - quantidade
                                    estoque.save()
                                compra.save()
                                email_mark = ''
                                email_rh = ''
                                user = User.objects.all()
                                for usuario_gestao in user:
                                    if usuario_gestao.username == 'marketing':
                                        email_mark = usuario_gestao.email
                                    if usuario_gestao.username == 'rh':
                                        email_rh = usuario_gestao.email
                                valor_total = f"{valor_total:.2f}".replace('.', ',')
                                if produto.tipo == 'Ingresso':
                                    enviar_email(f'Compra de Colaborador {colaborador.nome} finalizada com sucesso!',
                                                email_rh, produtos_adicionados, valor_total, colaborador.nome, data)
                                    enviar_email(f'A sua compra foi finalizada com sucesso!',
                                                colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                                elif produto.tipo == 'Camiseta':
                                    print("a")
                                    enviar_email(f'Compra de Colaborador {colaborador.nome} finalizada com sucesso!',
                                                email_mark, produtos_adicionados, valor_total, colaborador.nome, data)
                                    enviar_email(f'A sua compra foi finalizada com sucesso!',
                                                colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                                else:
                                    enviar_email(f'A sua compra foi finalizada com sucesso!',
                                                colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                                total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                                    colaborador)
                                return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador})
                            total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                                colaborador)
                            return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador})
                        messages.error(request, 'Senha incorreta!',
                           extra_tags='erro_inativo')
                        url = reverse('conveniencia')
                        return redirect(url)
                    messages.error(request, 'Colaborador está inativo!',
                           extra_tags='erro_inativo')
                    url = reverse('conveniencia')
                    return redirect(url)
                messages.error(request, 'Colaborador não cadastrado!',
                           extra_tags='erro_inativo')
            url = reverse('conveniencia')
            return redirect(url)

def Verificar_referencia_codigo(request):
    cap = cv2.VideoCapture(0)
    cap.set(3, 640)
    cap.set(4, 480)
    camera = True
    itens = request.session['itens']
    while camera == True:
        sucess, frame = cap.read()
        cv2.imshow('Testando', frame)
        cv2.waitKey(1)
        if cv2.waitKey(1) & 0xFF == 27:
            cap.release() # Libera o dispositivo de captura (a câmera)
            cv2.destroyAllWindows() # Fecha a janela
            break
        for code in decode(frame):
            codigo = code.data.decode('utf-8')
            if codigo:
                cap.release()
                cv2.destroyAllWindows()
                colaborador = Colaborador.objects.filter(codigo=codigo).first()
                produtos_adicionados = request.session.get('produtos', [])
                valor_total = request.session.get('valor_total', 0)
                itens = request.session.get('itens', 0)
                if colaborador:
                    if colaborador.ativo:
                        if colaborador.ativo:
                            total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                                colaborador)
                            return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total})
                        return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Senha incorreta!'})
                    return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador está inativo!'})
                return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador não cadastrado!'})
            return redirect('conveniencia')


def Adicionar_produto(request):
    if request.method == 'POST':
        codigo_barras = request.POST.get('codigo_barras')
        produto_codigo_barras = Produto.objects.filter(
            codigo_barras=codigo_barras)
        if not produto_codigo_barras:    # Verifica se o produto existe
            produtos_adicionados = request.session.get('produtos', [])
            valor_total = request.session.get('valor_total', 0)
            messages.error(request, 'Código de barras inválido!',
                           extra_tags='erro_inativo')
            url = reverse('conveniencia')
            return redirect(url)
        produto = get_object_or_404(Produto, codigo_barras=codigo_barras)

        if not produto.ativo:
            messages.error(request, 'Produto está inativo!',
                           extra_tags='erro_inativo')
            url = reverse('conveniencia')
            return redirect(url)

        if 'produtos' not in request.session:   # Cria a instância da compra se ainda não existir na sessão
            request.session['produtos'] = []
            request.session['valor_total'] = 0
            request.session['itens'] = 0

        # Verifica se o produto já foi adicionado anteriormente
        produtos = request.session['produtos']
        produto_existente = None
        for produto_data in produtos:
            if str(produto_data['codigo_barras']) == str(codigo_barras):
                produto_existente = produto_data
                break
        estoque = get_object_or_404(Estoque, produtos=produto)
        if estoque.quantidade <= 0:
            messages.error(request, 'Estoque indisponível!',
                           extra_tags='erro_inativo')
            url = reverse('conveniencia')
            return redirect(url)

        if produto_existente:
            # Incrementa a quantidade do produto existente
            produto_existente['quantidade'] += 1
            produto_existente['preco_total'] = produto_existente['preco'] * \
                produto_existente['quantidade']

            if estoque.quantidade < produto_existente['quantidade']:
                messages.error(request, 'Estoque indisponível!',
                               extra_tags='erro_inativo')
                url = reverse('conveniencia')
                return redirect(url)
        else:                                 # Caso o produto ainda não tenha sido adicionado, cria um novo registro na lista de produtos
            contador = len(produtos) + 1      # Atribui um identificador único
            preco = f"{produto.preco:.2f}".replace('.', ',')
            produto_data = {
                'id': contador,
                'nome': produto.nome,
                'codigo_barras': produto.codigo_barras,
                'preco': preco,
                'quantidade': 1,
                'preco_total': produto.preco
            }
            produtos.append(produto_data)

        # Atualiza o valor total da compra na sessão
        valor_total = request.session['valor_total']
        valor_total += produto.preco
        request.session['valor_total'] = valor_total

        itens = request.session['itens']
        itens += 1
        request.session['itens'] = itens

        return redirect('conveniencia')

    # Obtém a lista de produtos adicionados na sessão
    produtos_adicionados = request.session.get('produtos', [])
    # Obtém o valor total da compra na sessão
    valor_total = request.session.get('valor_total', 0)
    valor_total = f"{valor_total:.2f}".replace('.', ',')
    itens = request.session.get('itens', 0)
    # Renderiza a página com os produtos adicionados e o valor total
    return render(request, 'compra/conveniencia.html', {'produtos_adicionados': produtos_adicionados, 'valor_total': valor_total, 'itens': itens})

def calcular_gastos_referencia(colaborador):
    hoje = datetime.now().date()
    mes_passado = (hoje.month - 1) % 12 + 1
    mes_atual = (hoje.month) % 12 + 1
    ano = hoje.year

    # Calcula as datas de referência
    referencia_anterior_inicio = datetime(ano, mes_passado - 1, 26, 00, 00)
    referencia_anterior_fim = datetime(
        ano if mes_passado != 12 else ano - 1, mes_passado, 25, 23, 59)
    referencia_atual_inicio = datetime(ano, mes_passado, 26, 00, 00)
    referencia_atual_fim = datetime(
        ano if mes_atual != 12 else ano - 1, mes_atual, 25, 23, 59)

    # Consulta o histórico de compras do colaborador na referência anterior
    compras_referencia_anterior = Compra.objects.filter(
        colaborador=colaborador,
        data__range=[referencia_anterior_inicio, referencia_anterior_fim]
    )
    total_gasto_referencia_anterior = sum(
        compra.valor_total for compra in compras_referencia_anterior)

    # Consulta o histórico de compras do colaborador na referência atual
    compras_referencia_atual = Compra.objects.filter(
        colaborador=colaborador,
        data__range=[referencia_atual_inicio, referencia_atual_fim]
    )
    total_gasto_referencia_atual = sum(
        compra.valor_total for compra in compras_referencia_atual)

    total_gasto_referencia_anterior = f"{total_gasto_referencia_anterior:.2f}".replace(
        '.', ',')
    total_gasto_referencia_atual = f"{total_gasto_referencia_atual:.2f}".replace(
        '.', ',')

    return total_gasto_referencia_anterior, total_gasto_referencia_atual


def Finalizar_compra(request):
    itens = request.session['itens']
    if request.method == 'POST':
        produtos_adicionados = request.session.get('produtos', [])
        valor_total = request.session.get('valor_total', 0)
        valor_total = float(valor_total)
        quantidade = request.session.get('quantidade', 0)
        login = request.POST['login']
        senha = request.POST['senha']
        colaborador = Colaborador.objects.filter(login=login).first()
        if produtos_adicionados == []:
            messages.error(request, 'Carrinho vazio! Por favor, adicione um produto para realizar a compra',
                    extra_tags='erro_inativo')
            url = reverse('conveniencia')
            return redirect(url)
        if colaborador:
            if colaborador.ativo:
                if check_password(senha, colaborador.senha):
                    if valor_total > 0:

                        # Cria a nova compra e adiciona os produtos
                        compra = Compra.objects.create(
                            data=datetime.now(), valor_total=valor_total, colaborador=colaborador)
                        data = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                        for produto_data in produtos_adicionados:
                            produto = get_object_or_404(
                                Produto, codigo_barras=produto_data['codigo_barras'])
                            quantidade = produto_data['quantidade']
                            preco = produto.preco
                            item_compra = Item_Compra.objects.create(
                                compra=compra, produto=produto, preco=preco, quantidade=quantidade)
                            # Adiciona o produto à relação ManyToMany
                            compra.produtos.add(produto)
                        # Limpa a lista de produtos na sessão
                        request.session['produtos'] = []
                        # Reseta o valor total da compra na sessão
                        request.session['valor_total'] = 0
                        # Reseta os itens na sessão
                        request.session['itens'] = 0
                        # Atualiza a quantidade no estoque
                        if not produto.tipo == 'Ingresso' and not produto.tipo == 'Camiseta':
                            estoque = Estoque.objects.get(produtos=produto)
                            estoque.quantidade = F('quantidade') - quantidade
                            estoque.save()
                        compra.save()
                        email_mark = ''
                        email_rh = ''
                        user = User.objects.all()
                        for usuario_gestao in user:
                            if usuario_gestao.username == 'marketing':
                                email_mark = usuario_gestao.email
                            if usuario_gestao.username == 'rh':
                                email_rh = usuario_gestao.email
                        valor_total = f"{valor_total:.2f}".replace('.', ',')
                        if produto.tipo == 'Ingresso':
                            enviar_email(f'Compra de Colaborador {colaborador.nome} finalizada com sucesso!',
                                         email_rh, produtos_adicionados, valor_total, colaborador.nome, data)
                            enviar_email(f'A sua compra foi finalizada com sucesso!',
                                         colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                        elif produto.tipo == 'Camiseta':
                            print("a")
                            enviar_email(f'Compra de Colaborador {colaborador.nome} finalizada com sucesso!',
                                         email_mark, produtos_adicionados, valor_total, colaborador.nome, data)
                            enviar_email(f'A sua compra foi finalizada com sucesso!',
                                         colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                        else:
                            enviar_email(f'A sua compra foi finalizada com sucesso!',
                                         colaborador.email, produtos_adicionados, valor_total, colaborador.nome, data)
                        total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                            colaborador)
                        return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador})
                    total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                        colaborador)
                    return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador})
                valor_total = f"{valor_total:.2f}".replace('.', ',')
                return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Senha incorreta!'})
            valor_total = f"{valor_total:.2f}".replace('.', ',')
            return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador está inativo!'})
        valor_total = f"{valor_total:.2f}".replace('.', ',')
        return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador não cadastrado!'})
    return redirect('conveniencia')


def enviar_email(messagem, para_email, produtos_adicionados, valor_total, nome, data_compra):
    # Cria um objeto PDF
    response = HttpResponse()
    response['Content-Type'] = 'application/pdf'
    response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'
    response[
        'Content-Disposition'] = f'attachment; filename="SciRelatorioConsumoColaborador{nome}.pdf"'
    p = canvas.Canvas(response)

    imagem_path = 'static/imagens/logo-sci-ofc.png'

    imagem = Image.open(imagem_path)

    data_hora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 10)
    p.drawCentredString(540, 820, data_hora)
    p.setFont("Helvetica-Bold", 15)
    cor = '#000059'
    p.setFillColor(cor)
    p.drawCentredString(300, 800, "Relatório de Compra - Conveniência 2.0")

    p.drawImage(imagem_path, 50, 770, 85, 50, mask='auto')
    p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica", 12)
    y = 700
    p.drawString(
        50, 730, f"Colaborador: {nome}")
    cor = '#A9A9A9'
    p.setFillColor(cor)
    p.drawString(
        40, 715, "____________________________________________________________________________")
    p.setFillColorRGB(0, 0, 0)
    for produto_data in produtos_adicionados:
        produto = get_object_or_404(
            Produto, codigo_barras=produto_data['codigo_barras'])
        quantidade = produto_data['quantidade']
        preco = produto.preco
        preco_formh = f"{preco:.2f}".replace('.', ',')
        preco_form = f"{preco:.2f}".replace('.', ',')

        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, 680, f"Produto")
        p.drawString(210, 680, f"Quantidade")
        p.drawString(310, 680, f"Preço")
        p.drawString(380, 680, f"Data da Compra")
        cor = '#D3D3D3'
        p.setFont("Helvetica", 12)
        p.setFillColor(cor)
        p.drawString(
            48, 673, "____________________________________________________________________")
        p.setFillColorRGB(0, 0, 0)
        p.drawString(50, y - 50, f"{produto}")
        p.drawString(264, y - 50, f"{quantidade}")
        p.drawString(300, y - 50, f"R$ {preco_formh}")
        p.drawString(370, y - 50, f"{data_compra}")
        y -= 30
        cor = '#D3D3D3'
        p.setFillColor(cor)
        p.drawString(
            48, y-30, "____________________________________________________________________")
        p.setFillColorRGB(0, 0, 0)
        p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y-50, f"Valor total:")
    p.drawString(115, y-50, f"R$ {valor_total}")

    p.showPage()
    p.save()
    subject = 'Conveniência 2.0 - Relatório de consumo'
    message = messagem
    from_email = 'testeacademia@sci.com.br'
    to_email = para_email

    email_template = 'compra/msg_email.html'
    email_context = {
        'subject': subject,
        'message': message,
        'data': data_compra,
        'produtos_adicionados': [
            {
                'nome': produto_data['nome'],
                'quantidade': produto_data['quantidade'],
                'preco': produto_data['preco']
            }
            for produto_data in produtos_adicionados
        ],
        'valor_total': valor_total
    }
    email_html = render_to_string(
        email_template, email_context)

    email_text = strip_tags(email_html)
    email = EmailMultiAlternatives(
        subject, email_text, from_email, [to_email])
    email.attach_alternative(email_html, 'text/html')
    email.attach('relatorio.pdf',
                 response.getvalue(), 'application/pdf')
    email.send()


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
                    total_gasto_referencia_anterior, total_gasto_referencia_atual = calcular_gastos_referencia(
                        colaborador)
                    return render(request, 'compra/conveniencia.html', {'mostrar_ref': True, 'gasto_referencia_anterior': total_gasto_referencia_anterior, 'gasto_referencia_atual': total_gasto_referencia_atual, 'colaborador': colaborador, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total})
                return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Senha incorreta!'})
            return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador está inativo!'})
        return render(request, 'compra/conveniencia.html', {'mostrar_cad': True, 'login': login, 'produtos_adicionados': produtos_adicionados, 'itens': itens, 'valor_total': valor_total, 'erro': 'Colaborador não cadastrado!'})
    return redirect('conveniencia')


@login_required(login_url='login')
def Historico(request):
    compras = Compra.objects.all()

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
    # Obtém a lista de produtos adicionados na sessão
    produtos_adicionados = request.session.get('produtos', [])

    produto_excluido = None
    for produto in produtos_adicionados:
        if produto['id'] == produto_id:
            produto_excluido = produto
            break
    preco_produto = float(produto_excluido['preco'].replace(',', '.'))
    if produto_excluido:
        # Se o produto for excluído e possuir a qtd maior que 1, atualiza a quantidade e o valor total
        if produto_excluido['quantidade'] > 1:
            # Diminui a quantidade do produto em 1
            produto_excluido['quantidade'] -= 1
            # Atualiza o valor total da compra
            valor_total = request.session.get('valor_total', 0)
            valor_total -= preco_produto
            request.session['valor_total'] = valor_total
            # Atualiza a quantidade de itens da compra
            itens = request.session.get('itens', 0)
            itens -= 1
            request.session['itens'] = itens
        else:
            # Se a quantidade do produto for igual a 1, remove o produto da lista
            produtos_adicionados.remove(produto_excluido)
            # Atualiza o valor total da compra
            valor_total = request.session.get('valor_total', 0)
            valor_total -= preco_produto
            request.session['valor_total'] = valor_total
            # Atualiza a quantidade de itens da compra
            itens = request.session.get('itens', 0)
            itens -= 1
            request.session['itens'] = itens

    return redirect('conveniencia')


def Relatorio_consumo(request):
    if request.method == 'POST':
        data_inicio = request.POST.get('data_inicio')
        data_fim = request.POST.get('data_fim')
        colaborador_pesquisa = request.POST.get('colaborador_pesquisa')
        email = request.POST.get('email_ch')
        colaborador_pesquisa = Colaborador.objects.filter(
            login=colaborador_pesquisa).first()

        if data_inicio:
            data_inicio = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            print(data_inicio)
        if data_fim:
            data_fim = datetime.strptime(data_fim, "%Y-%m-%d").date()
            data_fim = data_fim + timedelta(days=1)
            print(data_fim)

        compras = Compra.objects.all()
        if data_inicio and data_fim:
            compras = compras.filter(
                data__range=[data_inicio, data_fim - timedelta(seconds=1)])
        if not colaborador_pesquisa:
            messages.error(request, 'Colaborador não encontrado!',
                           extra_tags='colab_nao_encontrado')
            url = reverse('relatorio_consumo')
            url += f'?data_inicio={data_inicio}&data_fim={data_fim}'
            return redirect(url)
        else:
            compras = compras.filter(
                colaborador__nome__icontains=colaborador_pesquisa)

        response = HttpResponse()
        selected_formats = []
        if 'formato_pdf' in request.POST:
            selected_formats.append('pdf')
        if 'formato_txt' in request.POST:
            selected_formats.append('txt')
        if not 'formato_pdf' in request.POST and not 'formato_txt' in request.POST:
            messages.error(request, 'Selecione uma opção de formato!',
                           extra_tags='colab_nao_encontrado')
            url = reverse('relatorio_consumo')
            print(colaborador_pesquisa)
            url += f'?data_inicio={data_inicio}&data_fim={data_fim}&colaborador_pesquisa={colaborador_pesquisa}'
            return redirect(url)

        if 'formato_pdf' in request.POST or 'formato_txt' in request.POST:
            response[
                'Content-Disposition'] = f'attachment; filename="SciRelatorioConsumoColaborador{colaborador_pesquisa}"'
            if 'pdf' in selected_formats and 'txt' in selected_formats:
                messages.error(
                    request, 'Selecione apenas uma opção de formato!', extra_tags='colab_nao_encontrado')
                url = reverse('relatorio_consumo')
                return redirect(url)
            if 'pdf' in selected_formats:
                response['Content-Type'] = 'application/pdf'
                response['Content-Disposition'] += '.pdf'
                p = canvas.Canvas(response)

                imagem_path = 'static/imagens/logo-sci-ofc.png'

                imagem = Image.open(imagem_path)

                data_hora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                p.setFont("Helvetica", 9)
                p.drawCentredString(540, 820, data_hora)
                cor = "#00008B"
                p.setFillColor(cor)
                p.setFont("Helvetica-Bold", 14)
                p.drawCentredString(300, 800, "Relatório de Consumo Detalhado")

                p.drawImage(imagem_path, 50, 770, 85, 50, mask='auto')
                p.setFillColorRGB(0, 0, 0)
                p.setFont("Helvetica", 12)
                y = 700
                if compras:
                    for compra in compras:
                        colaborador = compra.colaborador
                        valor_total = compra.valor_total
                        data = compra.data.strftime("%d-%m-%Y %H:%M:%S")
                        valor_total = f"{valor_total:.2f}".replace('.', ',')
                        for item in compra.item_compra_set.all():
                            p.drawString(
                                50, 730, f"Colaborador: {colaborador.nome}")
                            cor = '#D3D3D3'
                            p.setFillColor(cor)
                            p.drawString(
                                40, 710, "____________________________________________________________________________")
                            p.setFillColorRGB(0, 0, 0)
                            p.drawString(63, 680, f"Data da compra")
                            p.drawString(210, 680, f"Produtos")
                            p.drawString(350, 680, f"Quantidade")
                            p.drawString(450, 680, f"Valor total")
                            p.drawString(50, y - 50, f"{data}")
                            p.drawString(210, y - 50, f"{item.produto}")
                            p.drawString(400, y - 50, f"{item.quantidade}")
                            p.drawString(450, y - 50, f"R$ {valor_total}")
                            y -= 30
                            cor = '#D3D3D3'
                            p.setFillColor(cor)
                            p.drawString(
                                48, y-30, "____________________________________________________________________")
                            p.setFillColorRGB(0, 0, 0)
                else:
                    messages.error(request, 'Relatório não retorna dados!',
                                   extra_tags='colab_nao_encontrado')
                    url = reverse('relatorio_consumo')
                    return redirect(url)
                p.showPage()
                p.save()

            if 'txt' in selected_formats:
                response['Content-Type'] = 'text/plain'
                response['Content-Disposition'] += '.txt'
                content = ''
                data_hora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                content += f"{data_hora}\n"
                content += "SCI - Relatório de Consumo Detalhado\n\n"
                for compra in compras:
                    colaborador = compra.colaborador
                    valor_total = compra.valor_total
                    valor_total = f"{valor_total:.2f}".replace('.', ',')
                    data = compra.data.strftime("%d-%m-%Y")
                    content += f"Colaborador: {colaborador.nome}\n"
                    content += f"Data da compra: {data}\n"
                    content += f"Valor total: R${valor_total}\n\n"

                response.write(content)

            if email:
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    subject = 'Conveniência SCI - Relatório Consumo Detalhado'
                    message = 'Seu relatório de consumo detalhado foi gerado com sucesso!'
                    from_email = 'testeacademia@sci.com.br'
                    to_email = 'gabriellealicr@gmail.com'

                    email_template = 'relatorios/relatorio_consumo_email.html'
                    email_context = {
                        'subject': subject,
                        'message': message,
                    }
                    email_html = render_to_string(
                        email_template, email_context)

                    email_text = strip_tags(email_html)
                    email_message = EmailMultiAlternatives(
                        subject, email_text, from_email, [to_email])
                    email_message.attach_alternative(email_html, 'text/html')

                    if 'pdf' in selected_formats:
                        email_message.attach(f'SciRelatorioConsumoColaborador{colaborador_pesquisa}.pdf',
                                             response.getvalue(), 'application/pdf')

                    if 'txt' in selected_formats:
                        email_message.attach(f'SciRelatorioConsumoColaborador{colaborador_pesquisa}.txt',
                                             response.getvalue(), 'text/plain')

                    email_message.send()
                else:
                    messages.error(request, 'Informe um e-mail válido!',
                                   extra_tags='colab_nao_encontrado')
                    url = reverse('relatorio_consumo')
                    return redirect(url)

        return response

    colaborador = Colaborador.objects.all()
    return render(request, 'relatorios/relatorio_consumo.html', {'colaboradores': colaborador})


def Relatorio_geral(request):
    if request.method == 'POST':
        hoje = datetime.now().date()
        mes_passado = (hoje.month - 1) % 12 + 1
        mes_atual = (hoje.month) % 12 + 1
        ano = hoje.year
        email = request.POST.get('email_ch')
        selected_format = request.POST.get('flexRadioDefault')
        imagem_path = 'static/imagens/logo-sci-ofc.png'
        imagem = Image.open(imagem_path)

        selected_formats = []
        if selected_format == 'ref_anterior':
            selected_formats.append('anterior')
        elif selected_format == 'ref_atual':
            selected_formats.append('atual')
        elif selected_format == 'ref_geral':
            selected_formats.append('geral')

        # Calcula as datas de referência
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

        # Cria um objeto PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="relatorio.pdf"'

        response = HttpResponse()
        if 'formato_pdf' in request.POST:
            selected_formats.append('pdf')
        if 'formato_txt' in request.POST:
            selected_formats.append('txt')
        if not 'formato_pdf' in request.POST and not 'formato_txt' in request.POST:
            messages.error(request, 'Selecione uma opção de formato!',
                           extra_tags='colab_nao_encontrado')
            url = reverse('relatorio_geral')
            return redirect(url)

        if 'formato_pdf' in request.POST or 'formato_txt' in request.POST:
            response['Content-Disposition'] = 'attachment; filename="RelatorioGeral"'
            if 'pdf' in selected_formats and 'txt' in selected_formats:
                messages.error(
                    request, 'Selecione apenas uma opção de formato!', extra_tags='colab_nao_encontrado')
                url = reverse('relatorio_geral')
                return redirect(url)

            if 'pdf' in selected_formats:
                response['Content-Type'] = 'application/pdf'
                response['Content-Disposition'] += '.pdf'
                p = canvas.Canvas(response)

                total_gasto_referencia_atual = f"{total_gasto_referencia_atual:.2f}".replace(
                    '.', ',')
                total_gasto_referencia_anterior = f"{total_gasto_referencia_anterior:.2f}".replace(
                    '.', ',')

                data_hora = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
                p.setFont("Helvetica", 9)
                p.drawCentredString(540, 820, data_hora)
                cor = '#000059'
                p.setFillColor(cor)
                p.setFont("Helvetica-Bold", 14)
                p.drawCentredString(300, 800, "Relatório de Consumo Geral")
                p.drawImage(imagem_path, 50, 770, 85, 50, mask='auto')
                p.setFillColor(colors.black)
                p.setFont("Helvetica", 12)

                if 'atual' in selected_formats:
                    p.drawString(
                        50, 720, f"Período referência atual: {date(ano, mes_passado - 1, 26).strftime('%d-%m')}/{date(ano if mes_atual != 12 else ano - 1, mes_atual - 1, 25).strftime('%d-%m')}")
                    p.drawString(
                        50, 700, f"Total consumido: R$ {total_gasto_referencia_atual}")
                elif 'anterior' in selected_formats:
                    p.drawString(
                        50, 720, f"Período referência anterior: {date(ano, mes_passado - 2, 26).strftime('%d-%m')}/{date(ano if mes_atual != 12 else ano - 1, mes_atual - 2, 25).strftime('%d-%m')}")
                    p.drawString(
                        50, 700, f"Total gasto na referência anterior: R$ {total_gasto_referencia_anterior}")
                elif 'geral' in selected_formats:
                    p.drawString(
                        50, 720, f"Período referência anterior: {date(ano, mes_passado - 2, 26).strftime('%d-%m')}/{date(ano if mes_atual != 12 else ano - 1, mes_atual - 2, 25).strftime('%d-%m')}")
                    p.drawString(
                        50, 700, f"Total gasto na referência anterior: R$ {total_gasto_referencia_anterior}")
                    p.drawString(
                        50, 680, f"Período referência atual: {date(ano, mes_passado - 1, 26).strftime('%d-%m')}/{date(ano if mes_atual != 12 else ano - 1, mes_atual - 1, 25).strftime('%d-%m')}")
                    p.drawString(
                        50, 660, f"Total gasto na referência atual: R$ {total_gasto_referencia_atual}")

                # Finaliza o documento PDF
                p.showPage()
                p.save()

            if 'txt' in selected_formats:
                response['Content-Type'] = 'text/plain'
                response['Content-Disposition'] += '.txt'

                content = f"Total gasto na referência atual: R$ {total_gasto_referencia_atual}\n"

                response.write(content)

            if email:
                if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                    subject = 'Relatório Consumo Detalhado'
                    message = 'Conveniência 2.0 - Relatório de consumo'
                    from_email = 'testeacademia@sci.com.br'
                    to_email = 'gabriellealicr@gmail.com'

                    email_template = 'relatorios/relatorio_consumo_email.html'
                    email_context = {
                        'subject': subject,
                        'message': message,
                    }
                    email_html = render_to_string(
                        email_template, email_context)

                    email_text = strip_tags(email_html)
                    email_message = EmailMultiAlternatives(
                        subject, email_text, from_email, [to_email])
                    email_message.attach_alternative(email_html, 'text/html')

                    if 'pdf' in selected_formats:
                        email_message.attach('relatorio.pdf',
                                             response.getvalue(), 'application/pdf')

                    if 'txt' in selected_formats:
                        email_message.attach('relatorio.txt',
                                             response.getvalue(), 'text/plain')

                    email_message.send()
                else:
                    messages.error(request, 'Informe um e-mail válido!',
                                   extra_tags='colab_nao_encontrado')
                    url = reverse('relatorio_geral')
                    return redirect(url)

        return response

    return render(request, 'relatorios/relatorio_geral.html')
