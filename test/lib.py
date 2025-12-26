from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time


def login(selenium, device_user, device_password):

    selenium.open_app("/wp-login.php")

    user = selenium.find_by(By.ID, "user_login")
    user.send_keys(device_user)
    password = selenium.find_by(By.ID, "user_pass")
    password.send_keys(device_password)
    selenium.screenshot('login')
    password.send_keys(Keys.RETURN)
    
    selenium.find_by(By.XPATH, "//div[text()='Dashboard']")
  
    selenium.screenshot('login-complete')


def post(selenium):
    selenium.open_app("/wp-admin")
    selenium.click_by(By.XPATH, '//div[.="Posts"]')
    selenium.click_by(By.XPATH, '//a[.="Add Post"]')
    selenium.click_by(By.XPATH, '//button[@label="Close"]')
    post = selenium.find_by(By.XPATH, '//textarea[.="Post"]')
    post.send_keys("test post")


def read(selenium):
    selenium.open_app()
    selenium.find_by(By.XPATH, '//div[.="test post"]')

    
