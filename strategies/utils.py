import pandas as pd
import math
from marketdata.models import Symbol
import numpy as np
import matplotlib.pyplot as plt


def sharpe_ratio(returns_port_accum, annualized=True):
    sharpe = (returns_port_accum.mean() / returns_port_accum.std())

    return sharpe * (252*24 ** (1 / 2)) if annualized else sharpe


def volatility(ticker, log_retornos_periodo=5, limite=0.25, capital=500):
    symbol = Symbol.objects.get(ticker=ticker)
    data = symbol.quotes.values_list("close", flat=True).order_by("date")
    log_retornos = pd.Series(data)
    quotes = symbol.get_quotes(lookback="All")
    retornos_fechamento = quotes.close.diff()
    log_retornos = (log_retornos.apply(math.log).diff(1) * 100).fillna(0)
    log_retornos_acumulados = log_retornos.rolling(log_retornos_periodo).sum()
    log_retornos_acumulados.plot(figsize=(40, 20))
    plt.show()

    compra = (log_retornos_acumulados > -limite) & (log_retornos_acumulados.shift(1) < -limite)
    venda = (log_retornos_acumulados < limite) & (log_retornos_acumulados.shift(1) > limite)
    sinais = pd.Series(np.zeros(log_retornos.shape[0]))
    sinais[compra.values] = 1
    sinais[venda.values] = -1
    sinais[sinais == 0] = np.nan
    sinais = sinais.ffill().fillna(0)
    sinais.plot(figsize=(40, 20))
    plt.show()

    retornos_portifolio = retornos_fechamento.multiply(sinais.values, axis=0)
    resultado_acumulado = retornos_portifolio.cumsum() * symbol.pip_size * capital * symbol.tick_size
    sharpe_ratio = (retornos_portifolio.mean() / retornos_portifolio.std()) * (252 ** (1 / 2))
    resultado_acumulado.plot(figsize=(40, 20))
    plt.show()
    print(f"Retorno Total:{resultado_acumulado[-1]}")
    print(f"Sharpe Ratio Anualizado:{sharpe_ratio}")

    return retornos_portifolio, resultado_acumulado, sharpe_ratio, sinais
