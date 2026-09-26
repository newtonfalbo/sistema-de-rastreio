"""Aviso versionado do envio pontual. Alterar o texto exige nova versão."""
AVISO_VERSAO = '2026-09-26.1'
AVISO_TEXTO = (
    'Ao confirmar, autorizo o envio de uma única localização deste aparelho '
    '(coordenadas, precisão e horário), vinculada à pessoa e ao dispositivo informados, '
    'para consulta pelo responsável no painel de acompanhamento. '
    'Não há coleta em segundo plano. Posso desistir antes do envio desmarcando a autorização. '
    'Após o envio, a posição permanece no histórico; nesta versão de teste não há exclusão automática por prazo. '
    'Para solicitar exclusão ou interromper o compartilhamento, devo contatar o responsável que forneceu o acesso. '
    'O envio por link usa HTTPS intermediado pela Cloudflare durante o teste. '
    'O sistema registra este aviso, sua versão, o canal e o horário de recebimento da autorização.'
)


def aviso_envio():
    return {'versao': AVISO_VERSAO, 'texto': AVISO_TEXTO}
