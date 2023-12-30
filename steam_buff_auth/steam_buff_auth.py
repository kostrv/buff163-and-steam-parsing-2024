import os
import pickle
from time import sleep

try:
    from selenium import webdriver
except:
    os.system(f'pip install selenium')
    from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class Autorization():
    def __init__(self, steam_login: str, steam_password: str):
        '''
        Инициализация и первичная настройка параметров.
        '''
        self.steam_to_buff_login_link = 'https://steamcommunity.com/openid/loginform/?goto=%2Fopenid%2Flogin%3Fopenid.mode%3Dcheckid_setup%26openid.ns%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%26openid.realm%3Dhttps%253A%252F%252Fbuff.163.com%252F%26openid.sreg.required%3Dnickname%252Cemail%252Cfullname%26openid.assoc_handle%3DNone%26openid.return_to%3Dhttps%253A%252F%252Fbuff.163.com%252Faccount%252Flogin%252Fsteam%252Fverification%253Fback_url%253D%25252Faccount%25252Fsteam_bind%25252Ffinish%26openid.ns.sreg%3Dhttp%253A%252F%252Fopenid.net%252Fextensions%252Fsreg%252F1.1%26openid.identity%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%252Fidentifier_select%26openid.claimed_id%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%252Fidentifier_select%3Fopenid.mode%3Dcheckid_setup%26openid.ns%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%26openid.realm%3Dhttps%253A%252F%252Fbuff.163.com%252F%26openid.sreg_required%3Dnickname%252Cemail%252Cfullname%26openid.assoc_handle%3DNone%26openid.return_to%3Dhttps%253A%252F%252Fbuff.163.com%252Faccount%252Flogin%252Fsteam%252Fverification%253Fback_url%253D%25252Faccount%25252Fsteam_bind%25252Ffinish%26openid.ns_sreg%3Dhttp%253A%252F%252Fopenid.net%252Fextensions%252Fsreg%252F1.1%26openid.identity%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%252Fidentifier_select%26openid.claimed_id%3Dhttp%253A%252F%252Fspecs.openid.net%252Fauth%252F2.0%252Fidentifier_select'

        # Настройка вебдрайвера
        self.options = webdriver.ChromeOptions()
        self.options.add_argument('--lang=en-US')
        #self.options.add_argument('--headless') # По желанию, если не хотите, чтобы был виден весь процесс.
        
        self.driver = webdriver.Chrome(options=self.options)
        self.driver.maximize_window()
        
        self.timeout_time = 5
        self.wait = WebDriverWait(self.driver, self.timeout_time)
        
        self.steam_login = steam_login
        self.steam_password = steam_password

    def close_driver(self) -> None:
        '''
        Функция завершения работы и отключение процессов вебдрайвера.
        '''
        self.driver.close()
        self.driver.quit()
    
    def xpath_exists(self, xpath) -> bool:
        '''
        Функция для проверки нахождения элемента на странице по XPATH
        за счет использования исключения NoSuchElementException.
        '''
        try:
            self.driver.find_element(By.XPATH, xpath)
            exist = True
        except NoSuchElementException:
            exist = False
        return exist

    def entering_start_account_data(self) -> None:
        '''
        Функция для прохождения первого этапа авторизации (процесс ввода и проверки логина и пароля).
        Авторизация не будет пройдена, пока не будут введены правильные данные от аккаунта.
        '''
        # Поиск элементов авторизации.
        login_field = WebDriverWait(self.driver, self.timeout_time).until(
            EC.element_to_be_clickable((By.XPATH, '//input[@type="text" and @class="newlogindialog_TextInput_2eKVn"]'))
        )
        password_field = WebDriverWait(self.driver, self.timeout_time).until(

            EC.element_to_be_clickable((By.XPATH, '//input[@type="password" and @class="newlogindialog_TextInput_2eKVn"]'))
        )
        login_button = WebDriverWait(self.driver, self.timeout_time).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@type="submit" and @class="newlogindialog_SubmitButton_2QgFE"]'))
            )
        
        # Взаимодействия с элементами авторизации.
        login_field.clear()
        login_field.send_keys(self.steam_login)

        password_field.clear()
        password_field.send_keys(self.steam_password)
        sleep(1)

        login_button.click()
        sleep(3)
        
        # Обработка ввода неправильных данных авторизации.
        presence_of_incorrect_data: bool = self.xpath_exists('//div[@class="newlogindialog_FormError_1Mcy9" and contains(text(), "Please check your password and account name and try again")]')
        while presence_of_incorrect_data:
            print('==='*40)
            print('\nIncorrect account information entered!')
            self.steam_login = input('Type a vailid steam login: ')
            self.steam_password = input('Type a vailid password: ')

            # Повторение взаимодействия с элементами.
            sleep(1)
            login_field.clear()
            login_field.send_keys(self.steam_login)
            password_field.clear()
            password_field.send_keys(self.steam_password)
            sleep(1)
            
            login_button.click()
            sleep(3)

            presence_of_incorrect_data: bool = self.xpath_exists('//div[@class="newlogindialog_FormError_1Mcy9" and contains(text(), "Please check your password and account name and try again")]')

    def type_steam_guard_exist(self) -> None:
        '''
        Функция для прохождения второго этапа авторизации (процесс ввода, проверки стим-гуарда и дальнейшее продолжение).
        Обрабатываются различные исходы:
        - Использование для получения кода телефона
        - Использование для получения кода электронной почты 
        - Отсутствие двухфакторной ауентификации на аккаунте
        Подтверждение не будет пройдено, пока не будут введены правильные данные.
        '''
        sleep(5) 
        # Проверка появления окна ввода кода двухфакторной ауентификации.
        if self.xpath_exists('//div[@class="newlogindialog_AwaitingMobileConfText_7LmnT"]') or self.xpath_exists('//img[@src="https://community.akamai.steamstatic.com/public/images/applications/community/login_mobile_auth.png?v=e2f09e9d649508c82f214f84aba44363"]'):
            switch_auth_way_button = WebDriverWait(self.driver, self.timeout_time).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@class="newlogindialog_TextLink_1cnUQ newlogindialog_TextAlignCenter_2meUB"]'))
        )
            switch_auth_way_button.click()
        sleep(5)

        if self.xpath_exists('//div[@class="segmentedinputs_SegmentedCharacterInput_3PDBF Panel Focusable"]'): # Если поле ввода кода доступно.
            steam_guard_code = input('Type your steam guard code: ')
            while len(steam_guard_code) < 5: # Первичная проверка правильности кода.
                print('Incorrect steam guard code entered!')
                steam_guard_code = input('Type your steam guard code: ')
            
            # Ввод кода.
            steam_guard_code = [char for char in steam_guard_code][:5]
            steam_guard_code_entry_fields = self.driver.find_elements(By.XPATH, '//div[@class="segmentedinputs_SegmentedCharacterInput_3PDBF Panel Focusable"]//input[@class="segmentedinputs_Input_HPSuA Focusable"]')

            for i in range(len(steam_guard_code)):
                steam_guard_code_entry_fields[i].send_keys(steam_guard_code[i])
            sleep(3)
            
            # Полноценная проверка правильности введенного кода.
            presence_of_incorrect_steam_guard_code = self.xpath_exists('//div[@class="newlogindialog_FormError_1Mcy9" and contains(text(), "Incorrect code, please try again")]')
            while presence_of_incorrect_steam_guard_code:
                sleep(3)
                steam_guard_code_entry_fields = self.driver.find_elements(By.XPATH, '//div[@class="segmentedinputs_SegmentedCharacterInput_3PDBF segmentedinputs_Danger_3VXiO Panel Focusable"]//input[@class="segmentedinputs_Input_HPSuA Focusable"]')

                print('==='*40)
                print('Incorrect steam guard code entered!')
                steam_guard_code = input('Type a vailid steam guard code: ') # Повторное введение и проверка кода.
                while len(steam_guard_code) < 5:
                    print('Incorrect steam guard code entered!')
                    steam_guard_code = input('Type your steam guard code: ')

                steam_guard_code = [char for char in steam_guard_code][:5]
                sleep(4)
                
                # Очистка поля ввода.
                for i in range(len(steam_guard_code)):
                    steam_guard_code_entry_fields[i].clear()
                
                # Введение кода заного.
                for i in range(len(steam_guard_code)):
                    steam_guard_code_entry_fields[i].send_keys(steam_guard_code[i])
                    
                sleep(3)
                presence_of_incorrect_steam_guard_code = self.xpath_exists('//div[@class="newlogindialog_FormError_1Mcy9"]')
        
        # Окончательная проверка прохождения авторизации и сохранение куки.
        element = self.wait.until(EC.presence_of_element_located((By.XPATH, '//form[@enctype="multipart/form-data"]//input[@class="btn_green_white_innerfade"]')))
        if self.xpath_exists('//form[@enctype="multipart/form-data"]//input[@class="btn_green_white_innerfade"]'):
            print('Saving cookies...')
            pickle.dump(self.driver.get_cookies(), open(f'data\\{self.steam_login}_steam_auth_cookies', 'wb'))
        
    def log_into_steam(self) -> None:
        '''
        Компанующая функция авторизации стим в два этапа:
        - Этап первичной авторизации (процесс ввода и проверки логина и пароля)
        - Этап вторичной авторизации (процесс ввода, проверки стим-гуарда и дальнейшее продолжение)
        '''
        self.driver.get(self.steam_to_buff_login_link)
        self.entering_start_account_data()
        self.type_steam_guard_exist()
  
    def set_cookies(self) -> None:
        '''
        Функция для установки куки авторизации стим.
        Если возникает ошибка (отсутствие самих файлов в дериктории их повреждение или неактуальность),
        вызывается метод авторизации в стим аккаунт.
        '''   
        try:
            print('Trying to setup cookies...')
            for cookie in pickle.load(open(f'data\\{self.steam_login}_steam_auth_cookies', 'rb')):
                self.driver.add_cookie(cookie)  
            print('Сookies were successfully installed.')
            
        except Exception as error: # Если не получается использовать файлы куки
            print(f'There are issues with setting up cookies: {error}')
            print(f'Logging into steam {self.steam_login} account...')
            self.log_into_steam()
            
    def set_steam_cookies(self) -> None:
        '''
        Авторизация начинается c установки куки, если oпepaция проходит успешно, 
        продолжаем и авторизуемся на баффе, иначе проходим авторизацию в стиме.
        '''
        self.driver.get(self.steam_to_buff_login_link)
        self.set_cookies() 
        self.driver.refresh()
        
        while True: # Проверка флагов прохождения авторизации стим.
            if not self.xpath_exists('//form[@enctype="multipart/form-data"]//input[@class="btn_green_white_innerfade"]') or self.xpath_exists('//div[@class="newlogindialog_Login_ZOBYq"]'):
                print('Authorisation Error!')
                print(f'Logging into steam {self.steam_login} ...')
                self.log_into_steam()
                
                print('Setting up cookies...')
                self.set_cookies()
                self.driver.refresh()
                
            else: break
        print('Steam autorization is Done!')
    
    def buff_autorization(self) -> None:
        print('Going to buff autorization...')
        if self.xpath_exists('//form[@enctype="multipart/form-data"]//input[@class="btn_green_white_innerfade"]'):
            login_button = WebDriverWait(self.driver, self.timeout_time).until(
                EC.element_to_be_clickable((By.XPATH, '//form[@enctype="multipart/form-data"]//input[@class="btn_green_white_innerfade"]'))
            )
            login_button.click()
            print('Buff autorization is Done!') 
            
    def final_autorization(self) -> None:
        '''
        Компанующая функция основной авторизации
        '''
        self.set_steam_cookies()
        self.buff_autorization() 
        
operator = Autorization(steam_login=input('Type a vailid steam login: '), steam_password=input('Type a vailid password: '))

if __name__ == '__main__':
    try: operator.final_autorization()
    finally: operator.close_driver()