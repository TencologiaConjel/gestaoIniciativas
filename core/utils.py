from django.db.models import Q
from .models import Departamento  

REGRAS_PONTUACAO = {
    "tipo_beneficio": {"categoria": "valor", "pontuacao": {
        "horas_erros": 3,
        "receita": 5,
        "satisfacao_nps": 4,
        "compliance": 3,
        "outro": 1
    }},
    "publicos_impactados": {"categoria": "valor", "pontuacao": {
        "baixo": 1,    
        "medio": 3,    
        "alto": 5      
    }},
    "esforco_estimado": {"categoria": "esforco", "pontuacao": {
        "baixo": 1,
        "medio": 3,
        "alto": 5
    }},
}

def calcular_pontuacao(tipo_beneficio, esforco_estimado, total_departamentos):
    valor_total = 0
    esforco_total = 0

    valor_total += REGRAS_PONTUACAO['tipo_beneficio']['pontuacao'].get(tipo_beneficio, 0)
    if total_departamentos <= 3:
        valor_total += REGRAS_PONTUACAO['publicos_impactados']['pontuacao']['baixo']
    elif total_departamentos <= 6:
        valor_total += REGRAS_PONTUACAO['publicos_impactados']['pontuacao']['medio']
    else:
        valor_total += REGRAS_PONTUACAO['publicos_impactados']['pontuacao']['alto']

    esforco_total += REGRAS_PONTUACAO['esforco_estimado']['pontuacao'].get(esforco_estimado, 0)

    return valor_total, esforco_total


def classificar_ideia(valor, esforco):
    if valor >= 8 and esforco <= 3:
        return "Ganho Rápido"
    elif valor >= 8 and esforco > 3:
        return "Vale Investir"
    elif valor < 8 and esforco <= 3:
        return "Solução Simples"
    else:
        return "Aposte com Cuidado"

from .models import Colaborador

def is_gestor(user):
    """Verifica se o usuário é um gestor"""
    try:
        colaborador = Colaborador.objects.get(user=user)
        return colaborador.papel == 'gestor'
    except Colaborador.DoesNotExist:
        return False

def gestor_departamentos_ids(user):
    """Retorna os IDs dos departamentos que o gestor gerencia"""
    try:
        colaborador = Colaborador.objects.get(user=user)
        if colaborador.papel == 'gestor':
            return [colaborador.departamento.id]
        return []
    except Colaborador.DoesNotExist:
        return []
