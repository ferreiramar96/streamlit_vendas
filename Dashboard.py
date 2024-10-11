import streamlit as st
import requests
import pandas as pd 
import plotly.express as px

st.set_page_config(layout='wide', page_title='Vendas', page_icon=':shopping_trolley:')

def formata_numero(valor, prefixo=''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        else:
            valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('DASHBOARD DE VENDAS :shopping_trolley:')

url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o período', value=True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao':regiao.lower(), 'ano':ano}    

response = requests.get(url, params=query_string)
dados = pd.DataFrame.from_dict(response.json()) #transformar em um json e depois para um DF
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

#---------------------------------------------------------------------------------------------------#

## Tabelas
### Tabelas de Receita
receita_estados = dados.groupby('Local da compra')[['Preço']].sum() #Local de compra vira index
receita_estados = dados.drop_duplicates(subset='Local da compra')[['Local da compra', 'lat', 'lon']]\
                  .merge(receita_estados, left_on='Local da compra', right_index=True)\
                  .sort_values('Preço', ascending=False)

receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()

receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

### Tabelas de quantidade de vendas
qnt_vendas_estado = dados.groupby('Local da compra')[['Preço']].count()
qnt_vendas_estado = dados.drop_duplicates('Local da compra')[['Local da compra','lat','lon']]\
                    .merge(qnt_vendas_estado, left_on='Local da compra', right_index=True)\
                    .sort_values('Preço', ascending=False)
qnt_vendas_estado.rename(columns={'Preço': 'Quantidade'}, inplace=True)

qnt_venda_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='ME'))['Preço'].count().reset_index()
qnt_venda_mensal['Mes'] = qnt_venda_mensal['Data da Compra'].dt.month_name()
qnt_venda_mensal['Ano'] = qnt_venda_mensal['Data da Compra'].dt.year
qnt_venda_mensal.rename(columns={'Preço': 'Quantidade'}, inplace=True)

qnt_vendas_categoria = dados.groupby('Categoria do Produto')['Preço'].count().reset_index().sort_values('Preço', ascending=False)
qnt_vendas_categoria.rename(columns={'Preço':'Quantidade'}, inplace=True)

### Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

#---------------------------------------------------------------------------------------------------#

## Gráficos
fig_mapa_receita = px.scatter_geo(receita_estados, lat = 'lat', lon='lon',
                                  scope='south america', size='Preço',
                                  template='seaborn', hover_name='Local da compra',
                                  hover_data={'lat': False, 'lon': False},
                                  title='Receita por Estados')

fig_receita_mensal = px.line(receita_mensal, x='Mes', y='Preço',
                             markers=True, range_y=(0, receita_mensal['Preço'].max()),
                             color='Ano', line_dash='Ano',
                             title='Receita Mensal')
fig_receita_mensal.update_layout(yaxis_title='Receita')


fig_receita_estados = px.bar(receita_estados.head(), x='Local da compra', y='Preço',
                             text_auto=True, title='Top estados (receita)')
fig_receita_estados.update_layout(yaxis_title='Receita')


fig_receita_categorias = px.bar(receita_categorias, text_auto=True, title='Receira por categoria')
fig_receita_categorias.update_layout(yaxis_title='Receita')



fig_vendas_estado = px.scatter_geo(qnt_vendas_estado, lat='lat', lon='lon', scope='south america',
                                   size='Quantidade', template='seaborn', hover_name='Local da compra',
                                   hover_data={'lat':False, 'lon':False},
                                   title='Vendas por Estados')


fig_vendas_mensal = px.line(qnt_venda_mensal, x='Mes', y='Quantidade',
                             markers=True, range_y=(0, qnt_venda_mensal['Quantidade'].max()),
                             color='Ano', line_dash='Ano',
                             title='Quantidade Vendas')
fig_vendas_mensal.update_layout(yaxis_title='Quantidade Vendas')


fig_qnt_vendas_estado = px.bar(qnt_vendas_estado.head(), x='Local da compra', y='Quantidade', 
                               text_auto=True, title='Top estados (quantidade vendas)')
fig_qnt_vendas_estado.update_layout(yaxis_title='Vendas')


fig_qnt_vendas_categoria = px.bar(qnt_vendas_categoria.head(), x='Categoria do Produto', y='Quantidade', 
                               text_auto=True, title='Categoria (quantidade vendas)')
fig_qnt_vendas_categoria.update_layout(yaxis_title='Vendas')

#---------------------------------------------------------------------------------------------------#

## Visualização no streamlit
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width=True)
        st.plotly_chart(fig_receita_estados, use_container_width=True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categorias, use_container_width=True)

    st.dataframe(dados)

with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_vendas_estado)
        st.plotly_chart(fig_qnt_vendas_estado, use_container_width=True)

    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_vendas_mensal, use_container_width=True)
        st.plotly_chart(fig_qnt_vendas_categoria, use_container_width=True)

with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', min_value=2, max_value=10, value=5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores),
                                        x='sum', 
                                        y=vendedores[['sum']].sort_values('sum', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores),
                                        x='count', 
                                        y=vendedores[['count']].sort_values('count', ascending=False).head(qtd_vendedores).index,
                                        text_auto=True,
                                        title=f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores)