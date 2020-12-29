from day_counter import time_period
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from transliterate import translit
from tabulate import tabulate
from datetime import date

Base = declarative_base()


class Client(Base):
    """
    Создаём таблицу с клиентами и работаем с ней
    """
    __tablename__ = 'clients_info'

    id = Column(Integer, primary_key=True)
    operator_id = Column(Integer)
    fullname = Column(String)
    fullname_latin = Column(String)
    is_active = Column(Integer)
    birth_date = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    photo = Column(String)

    def get_allclients(self, oper_id):
        """
        Получаем полный список клиентов за всё время
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        if oper_id == 789561316:
            query_result = session.query(Client).filter(Client.operator_id == 822653560)
        else:
            query_result = session.query(Client).filter(Client.operator_id == oper_id)
        count_results = query_result.count()
        processed_list = list()
        for row in query_result:
            b_date = date.fromisoformat(row.birth_date).strftime('%d-%b-%Y')
            s_date = date.fromisoformat(row.start_date).strftime('%d/%m')
            processed_list.append(f'/id{row.id} <b>{row.fullname}</b>  {b_date}    <i>с {s_date}</i>')
        result = '\n\n'.join(processed_list) + '\n\n' + F'Всего: {count_results} чел.'
        session.close()
        return result

    def get_maxid(self):
        """
        Получаем максимальное значение id
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        query_result = session.query(func.max(Client.id))
        max_id_value = int(query_result.first()[0])
        session.close()
        return max_id_value

    def get_activeclients(self, oper_id):
        """
        Получаем всех текущих клиентов
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        if oper_id == 789561316:
            query_result = session.query(Client).filter(Client.operator_id == 822653560).filter(Client.is_active == 1)
        else:
            query_result = session.query(Client).filter(Client.operator_id == oper_id).filter(Client.is_active == 1)
        count_results = query_result.count()
        processed_list = list()
        for row in query_result:
            b_date = date.fromisoformat(row.birth_date).strftime('%d-%b-%Y')
            s_date = date.fromisoformat(row.start_date).strftime('%d/%m')
            processed_list.append(f'/id{row.id} <b>{row.fullname}</b>  {b_date}    <i>с {s_date}</i>')
        result = '\n\n'.join(processed_list) + '\n\n' + F'Всего: {count_results} чел.'
        session.close()
        return result

    def add_client(self, oper_id, fullname, birth_date, start_date, image_filename):
        """
        Добавляем нового клиента
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        client = Client()
        client.operator_id = oper_id
        client.fullname = fullname
        client.birth_date = birth_date
        client.is_active = 1
        client.fullname_latin = translit(client.fullname, 'ru', reversed=True)
        client.start_date = start_date
        client.photo = image_filename

        session.add(client)
        session.commit()

        confirmation = F'Новый клиент (# {client.id})  <b>{client.fullname}</b> ({client.fullname_latin})  с датой рождения  <code>{client.birth_date}</code>  был успешно добавлен!'
        session.close()
        return confirmation

    def activate_client(self, id, oper_id, start_date):
        """
        Устанавливаем статус клиента на активный
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        client = session.query(Client).filter(Client.operator_id == oper_id).filter(Client.id == id).first()
        client.operator_id = oper_id
        client.is_active = 1
        client.start_date = start_date
        client.end_date = ''
        session.commit()
        confirmation = f'{client.fullname} <b>АКТИВИРОВАН</b> с <code>{client.start_date}</code>'
        session.close()
        return confirmation

    def deactivate_client(self, id, oper_id, end_date):
        """
        Устанавливаем статус клиента на неактивный
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        client = session.query(Client).filter(Client.operator_id == oper_id).filter(Client.id == id).first()
        client.operator_id = oper_id
        client.is_active = 0
        client.end_date = end_date
        session.commit()
        work_period = time_period(client.fullname, client.birth_date, client.start_date, end_date)
        confirmation = work_period + "\n\n" + "Успешно <b>ДЕ-АКТИВИРОВАН</b>."
        session.close()
        return confirmation

    def search_clients(self, query):
        """
        Делаем запрос на поиск по имени клиента
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        query_result = session.query(Client).filter((Client.fullname_latin.like(f'%{query}%')) | (Client.id == query)).order_by(Client.is_active.desc())
        total_results = query_result.count()

        # Needed to not raise error when return more or less then 1 client
        client_id = ''
        client_status = ''
        photo = ''
        if not total_results:
            result = 'Ничего не было найдено, попробуйте снова'
        elif total_results == 1:
            client = query_result[0]
            client_id = client.id
            client_status = client.is_active
            photo = client.photo
            result = time_period(client.fullname, client.birth_date, client.start_date, client.end_date)
        else:
            processed_list = list()
            for row in query_result:
                b_date = date.fromisoformat(row.birth_date).strftime('%d-%b-%Y')
                s_date = date.fromisoformat(row.start_date).strftime('%d/%m')
                processed_list.append(f'/id{row.id} <b>{row.fullname}</b>  {b_date}    <i>с {s_date}</i>')
            result = '\n\n'.join(processed_list)
        session.close()
        return result, total_results, client_id, client_status, photo  # will send tuple (result, total_results, row.id). When found 1 record row.id will serve us for buttons,
        # in other cases is useless info we won't consider

    def get_reminderlist(self, oper_id):
        """
        Получаем всех текущих клиентов. Будем использовать этот список, для оповещения оператора о приближении даты оплаты
        """
        engine = create_engine('sqlite:///mmdb.db')
        Base.metadata.create_all(bind=engine)
        Session = sessionmaker(bind=engine)
        session = Session()
        query_result = session.query(Client).filter(Client.operator_id == oper_id).filter(Client.is_active == 1).all()
        session.close()
        reminder_list = list()
        for cl in query_result:
            cl_details = {
                'id': cl.id,
                'fullname': cl.fullname,
                'is_active': cl.is_active,
                'birth_date': cl.birth_date,
                'start_date': cl.start_date,
                'end_date': cl.end_date,
                'photo': cl.photo
            }
            reminder_list.append(cl_details)
        return reminder_list

    def __repr__(self):
        return f"<Client (fullname={self.fullname}, birth_date={self.birth_date})>"
