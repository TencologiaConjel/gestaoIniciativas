from django.contrib import admin

from .models import Departamento, Colaborador, Ideia, Risco


@admin.register(Departamento)
class DepartamentoAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']


@admin.register(Risco)
class RiscoAdmin(admin.ModelAdmin):
    list_display = ['nome']
    search_fields = ['nome']


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'papel', 'departamento']
    list_filter = ['papel', 'departamento']
    search_fields = ['nome', 'email']


@admin.register(Ideia)
class IdeiaAdmin(admin.ModelAdmin):
    list_display = ['titulo', 'tipo_beneficio', 'alinhamento_okr', 'esforco_estimado', 'patrocinador']
    list_filter = ['tipo_beneficio', 'alinhamento_okr', 'esforco_estimado', 'publicos_impactados']
    search_fields = ['titulo', 'descricao']
    filter_horizontal = ['publicos_impactados', 'equipes_necessarias', 'riscos_identificados']
    autocomplete_fields = ['patrocinador']
    readonly_fields = ['criado_em', 'atualizado_em']

