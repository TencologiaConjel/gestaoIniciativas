from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.models import Colaborador
from .models import Departamento, Risco, Ideia
from .utils import calcular_pontuacao, classificar_ideia, is_gestor
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')
        senha = request.POST.get('password')

        try:
            colaborador = Colaborador.objects.get(email=email)
            user = colaborador.user
        except Colaborador.DoesNotExist:
            user = None

        if user:
            user_autenticado = authenticate(request, username=user.username, password=senha)
            if user_autenticado:
                login(request, user_autenticado)
                return redirect('inicio')  
            else:
                messages.error(request, 'Senha incorreta.')
        else:
            messages.error(request, 'Usuário não encontrado.')

    return render(request, 'login.html')

@login_required
def cadastrar_ideia(request):
    if request.method == 'POST':
        titulo = request.POST.get('titulo')
        descricao = request.POST.get('descricao')
        tipo_beneficio = request.POST.get('tipo_beneficio')
        alinhamento_okr = request.POST.get('alinhamento_okr')
        esforco_estimado = request.POST.get('esforco_estimado')
        riscos_selecionados = request.POST.getlist('riscos_identificados')
        risco_outro_desc = request.POST.get('risco_outro_descricao')
        publicos_impactados = request.POST.getlist('publicos_impactados')
        equipes_necessarias = request.POST.getlist('equipes_necessarias')
        patrocinador_id = request.POST.get('patrocinador')
        metrica_sucesso = request.POST.get('metrica_sucesso')
        referencias = request.POST.get('referencias')

        if not titulo or not descricao or not tipo_beneficio or not alinhamento_okr or not esforco_estimado:
            messages.error(request, 'Preencha todos os campos obrigatórios.')
            return redirect('cadastrar_ideia')

        total_departamentos = len(publicos_impactados)
        valor_total, esforco_total = calcular_pontuacao(tipo_beneficio, esforco_estimado, total_departamentos)
        classificacao = classificar_ideia(valor_total, esforco_total)

        ideia = Ideia.objects.create(
            titulo=titulo,
            descricao=descricao,
            tipo_beneficio=tipo_beneficio,
            alinhamento_okr=alinhamento_okr,
            esforco_estimado=esforco_estimado,
            patrocinador_id=patrocinador_id if patrocinador_id else None,
            metrica_sucesso=metrica_sucesso,
            referencias=referencias,
            autor=request.user,
            valor_total=valor_total,
            esforco_total=esforco_total,
            classificacao=classificacao
        )

        ideia.riscos_identificados.set(riscos_selecionados)
        ideia.publicos_impactados.set(publicos_impactados)
        ideia.equipes_necessarias.set(equipes_necessarias)

        if "outro" in riscos_selecionados and risco_outro_desc:
            ideia.risco_outro_descricao = risco_outro_desc
            ideia.save()

        messages.success(request, 'Ideia cadastrada com sucesso!')
        return redirect('inicio')

    context = {
        'departamentos': Departamento.objects.all(),
        'riscos': Risco.objects.all(),
        'gestores': Colaborador.objects.filter(papel='gestor')
    }
    return render(request, 'nova_ideia.html', context)

@login_required
def inicio(request):
    total_ideias = Ideia.objects.count()
    ideias_aprovadas = Ideia.objects.filter(status='aprovada').count()
    minhas_ideias = Ideia.objects.filter(autor=request.user).order_by('-id')

    # DEBUG - Vamos ver o que está acontecendo
    print(f"DEBUG - Usuário: {request.user}")
    print(f"DEBUG - is_gestor result: {is_gestor(request.user)}")
    
    try:
        colaborador = Colaborador.objects.get(user=request.user)
        print(f"DEBUG - Colaborador: {colaborador}")
        print(f"DEBUG - Papel: {colaborador.papel}")
    except Colaborador.DoesNotExist:
        print("DEBUG - Colaborador não existe!")

    context = {
        'total_ideias': total_ideias,
        'ideias_aprovadas': ideias_aprovadas,
        'minhas_ideias': minhas_ideias,
        'eh_gestor': is_gestor(request.user),  # Adicionar esta linha
    }

    return render(request, 'inicio.html', context)

@login_required
def detalhe_ideia(request, pk):
    ideia = get_object_or_404(Ideia, pk=pk)
    user = request.user
    
    # Verifica se o usuário pode ver a ideia
    pode_ver = False
    
    # 1. Administrador pode ver tudo
    if user.is_staff or user.is_superuser:
        pode_ver = True
    
    # 2. Autor da ideia pode ver
    elif ideia.autor == user:
        pode_ver = True
    
    # 3. Patrocinador pode ver
    elif ideia.patrocinador and ideia.patrocinador.user == user:
        pode_ver = True
    
    # 4. Gestor dos departamentos envolvidos pode ver
    else:
        try:
            colaborador = Colaborador.objects.get(user=user)
            if colaborador.papel == 'gestor':
                # Verifica se o gestor está em algum dos departamentos das equipes necessárias
                eh_gestor_equipe = ideia.equipes_necessarias.filter(
                    id=colaborador.departamento.id
                ).exists()
                
                # Verifica se o gestor está em algum dos departamentos dos públicos impactados
                eh_gestor_publico = ideia.publicos_impactados.filter(
                    id=colaborador.departamento.id
                ).exists()
                
                pode_ver = eh_gestor_equipe or eh_gestor_publico
        except Colaborador.DoesNotExist:
            pode_ver = False
    
    if not pode_ver:
        raise PermissionDenied("Você não tem permissão para ver esta ideia.")

    context = {
        "ideia": ideia, 
        "eh_gestor": is_gestor(user)
    }
    
    return render(request, "detalhe_ideia.html", context)

@login_required
def ideias_minhas_equipes(request):
    user = request.user
    
    # Verifica se o usuário é gestor
    if not is_gestor(user):
        raise PermissionDenied("Apenas gestores podem acessar esta página.")
    
    try:
        colaborador = Colaborador.objects.get(user=user)
        
        # Busca ideias onde o departamento do gestor está envolvido
        ideias = (
            Ideia.objects
            .filter(
                Q(equipes_necessarias=colaborador.departamento) |
                Q(publicos_impactados=colaborador.departamento)
            )
            .select_related("autor", "patrocinador", "patrocinador__departamento")
            .prefetch_related("equipes_necessarias", "publicos_impactados")
            .distinct()
            .order_by("-criado_em")
        )
        
    except Colaborador.DoesNotExist:
        raise PermissionDenied("Colaborador não encontrado.")
    
    return render(request, "lista_minhas_equipes.html", {
        "ideias": ideias,
        "eh_gestor": True,
    })

@login_required
def minhas_ideias_visiveis(request):
    user = request.user
    
    minhas_ideias = Q(autor=user)
    
    if user.is_staff or user.is_superuser:
        ideias = Ideia.objects.all()
    else:
        try:
            colaborador = Colaborador.objects.get(user=user)
            
            patrocinadas = Q(patrocinador=colaborador)
            
            if colaborador.papel == 'gestor':
                dept_envolvido = Q(
                    Q(equipes_necessarias=colaborador.departamento) |
                    Q(publicos_impactados=colaborador.departamento)
                )
                ideias = Ideia.objects.filter(
                    minhas_ideias | patrocinadas | dept_envolvido
                ).distinct()
            else:
                ideias = Ideia.objects.filter(
                    minhas_ideias | patrocinadas
                ).distinct()
                
        except Colaborador.DoesNotExist:
            ideias = Ideia.objects.filter(minhas_ideias)
    
    ideias = ideias.select_related("autor", "patrocinador").prefetch_related(
        "equipes_necessarias", "publicos_impactados"
    ).order_by("-criado_em")
    
    return render(request, "minhas_ideias_visiveis.html", {
        "ideias": ideias,
        "eh_gestor": is_gestor(user)
    })

from django.contrib.auth import get_user_model
from django.http import HttpResponse

def create_admin(request):
    User = get_user_model()
    username = "admin"
    password = "Re301203@"

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username=username, email="", password=password)
        return HttpResponse("Superusuário criado com sucesso!")
    return HttpResponse("Superusuário já existe.")

