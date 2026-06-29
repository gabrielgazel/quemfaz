import sqlite3

def conecta_bd():
    conexao = sqlite3.connect('exames.db')
    return conexao

def inserir_dados(cod_tuss, nome_exame, quem_faz, tem_preparo):
    conexao = conecta_bd()
    cursor = conexao.cursor()
    
    cursor.execute('''
    INSERT INTO exames (cod_tuss, nome_exame, quem_faz, tem_preparo)
    VALUES (?, ?, ?, ?)
    ''', (cod_tuss, nome_exame, quem_faz, tem_preparo))
    
    conexao.commit()
    cursor.close()
    conexao.close()

def listar_dados():
    conexao = conecta_bd()
    cursor = conexao.cursor()
    
    cursor.execute('SELECT * FROM exames')
    dados = cursor.fetchall()
    
    cursor.close()
    conexao.close()
    
    return dados