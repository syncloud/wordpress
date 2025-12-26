from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC


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


def post_prev(selenium, first_time):
    selenium.open_app("/wp-admin")
    selenium.click_by(By.XPATH, '//div[.="Posts"]')
    selenium.click_by(By.XPATH, '//a[.="Add New"]')
    if first_time:
        selenium.click_by(By.XPATH, '//button[@aria-label="Close"]')
    selenium.screenshot('post-prev')
    #selenium.driver.switch_to.frame("editor-canvas")
    title = selenium.find_by(By.XPATH, "//h1[contains(@class, 'wp-block-post-title')]")
    title.send_keys("syncloud title")
    paragraph = selenium.find_by(By.XPATH, "//p[@aria-label='Add default block']")
    paragraph.send_keys("syncloud paragraph")
    #selenium.driver.switch_to.default_content()

    selenium.click_by(By.XPATH, "//button[.='Publish']")
    selenium.click_by(By.XPATH, "//button[.='Cancel']/../..//button[.='Publish']")
    selenium.find_by(By.XPATH, "//a[contains(., 'View Post')]")

def post_next(selenium, first_time):
    selenium.open_app("/wp-admin")
    selenium.click_by(By.XPATH, '//div[.="Posts"]')
    selenium.click_by(By.XPATH, '//a[.="Add Post"]')
    if first_time:
        selenium.click_by(By.XPATH, '//button[@aria-label="Close"]')
    selenium.driver.switch_to.frame("editor-canvas")
    title = selenium.find_by(By.XPATH, "//h1[contains(@class, 'wp-block-post-title')]")
    title.send_keys("syncloud title")
    paragraph = selenium.find_by(By.XPATH, "//p[@aria-label='Add default block']")
    paragraph.send_keys("syncloud paragraph")
    selenium.driver.switch_to.default_content()

    selenium.click_by(By.XPATH, "//button[.='Publish']")
    selenium.click_by(By.XPATH, "//button[.='Cancel']/../..//button[.='Publish']")
    selenium.find_by(By.XPATH, "//a[contains(., 'View Post')]")


def read(selenium):
    selenium.open_app()
    selenium.find_by(By.XPATH, '//a[.="syncloud title"]')
    selenium.find_by(By.XPATH, '//p[.="syncloud paragraph"]')

    
