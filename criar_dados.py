from app import app, db, Parceiro, Post


with app.app_context():
    
    db.drop_all()
    db.create_all()

    
    print("Criando parceiros...")
    p1 = Parceiro(nome="Parceiro Sem Logo", logo="") 
    
    db.session.add(p1)

    
    print("Criando posts...")
    post1 = Post(
        imagem_url="static/imagens/post1.jpeg", 
        link_post="https://www.instagram.com/p/DQnLwuHD4yv/?img_index=1", 
        legenda="Já conhece o subsistema de Direção e Suspensão?"
    )
    post2 = Post(
        imagem_url="static/imagens/post2.jpeg", 
        link_post="https://www.instagram.com/p/DMi6TN1ut00/?img_index=1", 
        legenda="Já ouviu falar no subsistema de Freios do Iaguary Baja?"
    )
    post3 = Post(
        imagem_url="static/imagens/post3.jpeg", 
        link_post="https://www.instagram.com/p/DLs0jXWvm9v/?img_index=1", 
        legenda="Já conhece o subsistema de Powertrain?"
    )

    db.session.add(post1)
    db.session.add(post2)
    db.session.add(post3)

   
    db.session.commit()
    print("Dados criados com sucesso! Agora o site vai mostrar as imagens.")
    
