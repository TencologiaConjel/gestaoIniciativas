from django.db import models
from django.contrib.auth.models import User


TIPO_BENEFICIO_CHOICES = [
    ('horas_erros', 'Horas/Erros'),
    ('receita', 'Receita'),
    ('satisfacao_nps', 'Satisfação/NPS'),
    ('compliance', 'Compliance'),
    ('outro', 'Outro'),
]

OKR_CHOICES = [
    ('prosperar', 'Prosperar nos negócios'),
    ('reter_clientes', 'Conquistar e reter clientes'),
    ('excelencia', 'Gerir com excelência'),
    ('desenvolver_profissionais', 'Desenvolver profissionais capacitados e senso de pertencimento'),
    ('outros', 'Outros'),
]

ESFORCO_CHOICES = [
    ('baixo', 'Baixo (<1 semana)'),
    ('medio', 'Médio (1-4 semanas)'),
    ('alto', 'Alto (>4 semanas)'),
]
STATUS_CHOICES = [
    ('avaliacao', 'Em Avaliação'),
    ('aprovada', 'Aprovada'),
    ('reprovada', 'Reprovada'),
]

class Departamento(models.Model):
    nome = models.CharField(max_length=80, unique=True)

    class Meta:
        ordering = ('nome',)

    def __str__(self):
        return self.nome


class Colaborador(models.Model):
    PAPEL_CHOICES = [
        ('gestor', 'Gestor'),
        ('colaborador', 'Colaborador'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=60)
    email = models.EmailField(unique=True)
    papel = models.CharField(max_length=15, choices=PAPEL_CHOICES)
    departamento = models.ForeignKey(
        Departamento, on_delete=models.CASCADE, related_name='colaboradores'
    )

    def __str__(self):
        return self.nome

    def is_gestor(self):
        return self.papel == 'gestor'

class Risco(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ('nome',)

    def __str__(self):
        return self.nome

class Ideia(models.Model):
    autor = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    titulo = models.CharField(max_length=120, blank=True, default="")
    descricao = models.TextField(verbose_name="Qual é a dor ou oportunidade?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Em Avaliação')
    publicos_impactados = models.ManyToManyField(
        Departamento,
        related_name='ideias_afetadas',
        blank=True,
        help_text="Departamentos afetados por essa ideia."
    )

    tipo_beneficio = models.CharField(max_length=30, choices=TIPO_BENEFICIO_CHOICES)
    alinhamento_okr = models.CharField(max_length=50, choices=OKR_CHOICES)
    esforco_estimado = models.CharField(max_length=10, choices=ESFORCO_CHOICES)

    riscos_identificados = models.ManyToManyField(Risco, related_name='ideias', blank=True)
    risco_outro_descricao = models.CharField(
        max_length=200, blank=True, null=True,
        help_text="Obrigatório se marcar 'Outro' nos riscos."
    )

    metrica_sucesso = models.TextField(blank=True)

    patrocinador = models.ForeignKey(
        Colaborador,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'papel': 'gestor'},
        related_name='ideias_patrocinadas'
    )

    equipes_necessarias = models.ManyToManyField(
        Departamento,
        related_name='ideias_com_equipe',
        blank=True,
        help_text="Departamentos necessários para execução da ideia."
    )

    referencias = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    valor_total = models.IntegerField(default=0)
    esforco_total = models.IntegerField(default=0)
    classificacao = models.CharField(max_length=50, blank=True)


    class Meta:
        ordering = ('-criado_em',)

    def __str__(self):
        return self.titulo or f"Ideia #{self.pk}"

    @property
    def gestores_envolvidos(self):
        departamentos = list(self.publicos_impactados.all()) + list(self.equipes_necessarias.all())
        return Colaborador.objects.filter(
            papel='gestor',
            departamento__in=departamentos
        ).distinct()
