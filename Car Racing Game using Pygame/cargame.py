import random
from time import sleep
from pikachu import Producer, Consumer
import pikachu
import pygame
import uuid
from car import Car
from TokenManger import TokenManager


class Button():
    def __init__(self, x, y, image, scale):
        width = image.get_width()
        height = image.get_height()
        self.image = pygame.transform.scale(
            image, (int(width * scale), int(height * scale)))
        self.rect = self.image.get_rect()
        self.rect.topleft = (x, y)
        self.clicked = False

    def pressed(self, surface):
        action = False
        # get mouse position
        pos = pygame.mouse.get_pos()

        # check mouseover and clicked conditions
        if self.rect.collidepoint(pos):
            if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
                self.clicked = True
                action = True

        if pygame.mouse.get_pressed()[0] == 0:
            self.clicked = False

        # draw button on screen
        surface.blit(self.image, (self.rect.x, self.rect.y))

        return action


class CarRacing:
    def __init__(self):
        pygame.init()
        self.display_width = 1000
        self.game_width = 800
        self.display_height = 600
        self.black = (0, 0, 0)
        self.white = (255, 255, 255)
        self.clock = pygame.time.Clock()
        self.gameDisplay = None
        # chat feature init
        self.chat_width = 200
        self.input_box = pygame.Rect(
            800, self.display_height - 40, self.chat_width - 20, 30)
        self.chat_font = pygame.font.Font(None, 24)
        self.chat_text = ""
        self.chat_active = False
        self.messages = []  # List to store chat messages
        token_manager = TokenManager(token_lifetime_minutes=30)
        global token
        token = token_manager.get()

        self.my_uuid = token["uuid"]
        self.event_exchange = "events"
        self.chat_exchange = "chat"
        self.id = None
        self.serverIp = "16.16.159.166"
        self.getMyID(self.serverIp, self.my_uuid, self.event_exchange)
        self.gameInit()

        # producer and consumer init
        self.producer = Producer(
            self.serverIp, serializer=pikachu.serializeJSON)
        self.consumer = Consumer(self.serverIp)
        self.consumer.subscribe(
            self.event_exchange, event_handler=self.handle_car_move, deserializer=pikachu.deserializeJSON)
        self.consumer.subscribe(
            self.chat_exchange, event_handler=self.handle_chat, deserializer=lambda x: x.decode('utf-8'))
        self.initialize()

    def getMyID(self, server, my_uuid, exchange):

        def handler(channel, method, properties, body):
            print(body)
            header = body.get("header")
            uuid = body.get("uuid")
            if header == "id-response" and uuid == my_uuid:
                self.id = body.get("id")

            if self.id is not None:
                consumer.stop_consuming(exchange=exchange)

        request_id_message = {
            "header": "id-request",
            "token": token
        }

        print("Request ID message:", request_id_message)
        producer = Producer(server, serializer=pikachu.serializeJSON)
        consumer = Consumer(server)
        consumer.subscribe(exchange, event_handler=handler,
                           deserializer=pikachu.deserializeJSON)
        producer.publish(exchange, request_id_message)
        consumer.listen()

    def handle_chat(self, channel, method, properties, body):
        self.messages.append(body)

    def handle_car_move(self, channel, method, properties, body):
        header = body.get("header")
        if header == "car_moved":
            print("car_moved")
            carId = body.get("id")
            if carId != self.id:
                print("carId:", carId)
                self.carsArr[carId].x = body.get("x")

    def initialize(self):
        self.screen = pygame.display.set_mode(
            (self.display_width, self.display_height))
        self.startImg = pygame.image.load('./img/start.png').convert_alpha()
        self.startButton = Button(350, 500, self.startImg, 0.5)
        self.LoginImg = pygame.image.load('./img/login.png').convert_alpha()
        self.loginButton = Button(600, 500, self.LoginImg, 0.5)
        textbox_width = 200
        textbox_height = 30
        textbox_x = (self.game_width - textbox_width) // 2
        textbox_y = (self.display_height - textbox_height) // 2
        self.textbox_rect = pygame.Rect(
            textbox_x, textbox_y, textbox_width, textbox_height)
        self.text = ""
        self.font = pygame.font.Font(None, 32)
        self.textbox_active = False

        label_text = "Enter your name"
        label_font = pygame.font.Font(None, 24)
        label_surface = label_font.render(label_text, True, self.black)
        label_x = textbox_x - label_surface.get_width() - 10
        label_y = textbox_y + 5

        self.run = True
        while self.run:
            self.screen.fill((202, 228, 241))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.textbox_rect.collidepoint(event.pos):
                        self.textbox_active = not self.textbox_active
                    else:
                        self.textbox_active = False
                    if self.input_box.collidepoint(event.pos):
                        self.chat_active = not self.chat_active
                    else:
                        self.chat_active = False
                elif event.type == pygame.KEYDOWN:
                    if self.textbox_active:
                        if event.key == pygame.K_RETURN:
                            self.textbox_active = False
                        elif event.key == pygame.K_BACKSPACE:
                            self.text = self.text[:-1]
                        else:
                            self.text += event.unicode
                    if self.chat_active:
                        if event.key == pygame.K_RETURN:
                            # Store chat message
                            if self.chat_text != "":
                                # pubish the message
                                self.producer.publish(
                                    self.chat_exchange, self.text + ": " + self.chat_text
                                )
                            self.chat_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.chat_text = self.chat_text[:-1]
                        else:
                            self.chat_text += event.unicode

            # Render and blit the chat messages
            y = 10
            for message in self.messages:
                text_surface = self.chat_font.render(message, True, self.black)
                self.screen.blit(text_surface, (self.game_width + 10, y))
                y += 30

            # Render and blit the chat input text
            text_surface = self.chat_font.render(
                self.chat_text, True, self.black)
            self.screen.blit(
                text_surface, (self.input_box.x + 5, self.input_box.y + 5))
            pygame.draw.rect(self.screen, self.black, self.input_box, 2)

            # Render and blit the label for name input
            self.screen.blit(label_surface, (label_x, label_y))

            self.textbox_rect.w = max(200, self.font.size(self.text)[0] + 10)

            pygame.draw.rect(self.screen, (255, 255, 255),
                             self.textbox_rect, 0)
            pygame.draw.rect(self.screen, (0, 0, 0), self.textbox_rect, 2)

            txt_surface = self.font.render(self.text, True, (0, 0, 0))
            self.screen.blit(
                txt_surface, (self.textbox_rect.x + 5, self.textbox_rect.y + 5))

            if (self.loginButton.pressed(self.screen)):
                print("connected")

            if (self.startButton.pressed(self.screen)):
                if (self.text != ""):
                    self.racing_window()
                    pygame.quit()
                else:
                    pass

            pygame.display.update()
            self.clock.tick(60)

        pygame.quit()

    def gameInit(self):
        self.carsArr = []
        self.crashed = False
        for i in range(3):
            car = Car()
            car.id = i
            car.image = pygame.image.load(f'./img/car{i+1}.png')
            car.x = self.game_width * (0.35 + 0.10*i)
            car.y = self.display_height * 0.8
            car.width = 47
            self.carsArr.append(car)
        self.myCar = self.carsArr[self.id]
        print(self.myCar.id)

        # enemy_rock
        self.enemy_rock = pygame.image.load('./img/rock.png')
        self.enemy_rock_startx = random.randrange(310, 450)
        self.enemy_rock_starty = -600
        self.enemy_rock_speed = 14
        self.enemy_rock_width = 50
        self.enemy_rock_height = 50

        # Background
        self.bgImg = pygame.image.load("./img/back_ground.jpg")
        self.bg_x1 = (self.game_width / 2) - (360 / 2)
        self.bg_x2 = (self.game_width / 2) - (360 / 2)
        self.bg_y1 = 0
        self.bg_y2 = -600
        self.bg_speed = 3
        self.count = 0

    def cars(self, carImg, car_x_coordinate, car_y_coordinate):
        self.gameDisplay.blit(carImg, (car_x_coordinate, car_y_coordinate))

    def racing_window(self):
        self.gameInit()
        self.gameDisplay = pygame.display.set_mode(
            (self.display_width, self.display_height))
        pygame.display.set_caption('racing game')
        self.run_car()

    def run_car(self):
        while not self.crashed:

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.crashed = True
                # print(event)
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.input_box.collidepoint(event.pos):
                        self.chat_active = not self.chat_active
                    else:
                        self.chat_active = False
                if self.chat_active:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN:
                            self.producer.publish(
                                self.chat_exchange, self.text + ": " + self.chat_text
                            )
                            self.chat_text = ""
                        elif event.key == pygame.K_BACKSPACE:
                            self.chat_text = self.chat_text[:-1]
                        else:
                            self.chat_text += event.unicode
                else:

                    if (event.type == pygame.KEYDOWN):
                        if (event.key == pygame.K_LEFT):
                            self.myCar.x -= 50
                            self.producer.publish(self.event_exchange, {"header": "car_moved",
                                                                        "id": self.myCar.id, "x": self.myCar.x})
                            print("CAR X COORDINATES: %s" % self.myCar.x)

                            # self.producer.publish(self.event_exchange, "left")
                        if (event.key == pygame.K_RIGHT):
                            self.myCar.x += 50
                            self.producer.publish(self.event_exchange, {"header": "car_moved",
                                                                        "id": self.myCar.id, "x": self.myCar.x})
                            print("CAR X COORDINATES: %s" % self.myCar.x)
                            # self.producer.publish(self.event_exchange, "right")
                        print("x: {x}, y: {y}".format(
                            x=self.myCar.x, y=self.myCar.y))

            self.gameDisplay.fill(self.white)
            self.back_ground_raod()

            self.run_enemy_rock(self.enemy_rock_startx, self.enemy_rock_starty)
            self.enemy_rock_starty += self.enemy_rock_speed

            if self.enemy_rock_starty > self.display_height:
                self.enemy_rock_starty = 0 - self.enemy_rock_height
                self.enemy_rock_startx = random.randrange(310, 450)

            for car in self.carsArr:
                self.cars(car.image, car.x, car.y)

            self.highscore(self.count)
            self.count += 1
            if (self.count % 100 == 0):
                self.bg_speed += 1
            if self.myCar.y < self.enemy_rock_starty + self.enemy_rock_height:
                if self.myCar.x > self.enemy_rock_startx and self.myCar.x < self.enemy_rock_startx + self.enemy_rock_width or self.myCar.x + self.myCar.width > self.enemy_rock_startx and self.myCar.x + self.myCar.width < self.enemy_rock_startx + self.enemy_rock_width:
                    if self.bg_speed > 0:
                        self.bg_speed -= 1
                        self.enemy_rock_starty = 900

            if self.myCar.x < 300 or self.myCar.x > 460:
                self.myCar.x = (self.display_width * 0.45)
                if self.bg_speed > 0:
                    self.bg_speed -= 1
        # Render and blit the chat messages
            y = 10
            for message in self.messages:
                text_surface = self.chat_font.render(message, True, self.black)
                self.screen.blit(text_surface, (self.game_width + 10, y))
                y += 30

            # Render and blit the chat input text
            text_surface = self.chat_font.render(
                self.chat_text, True, self.black)
            self.screen.blit(
                text_surface, (self.input_box.x + 5, self.input_box.y + 5))
            pygame.draw.rect(self.screen, self.black, self.input_box, 2)

            pygame.display.update()
            self.clock.tick(60)

    def display_message(self, msg):
        font = pygame.font.SysFont("comicsansms", 72, True)
        text = font.render(msg, True, (255, 255, 255))
        self.gameDisplay.blit(
            text, (400 - text.get_width() // 2, 240 - text.get_height() // 2))
        self.display_credit()
        pygame.display.update()
        self.clock.tick(60)
        sleep(1)
        car_racing.initialize()
        car_racing.racing_window()

    def back_ground_raod(self):
        self.gameDisplay.blit(self.bgImg, (self.bg_x1, self.bg_y1))
        self.gameDisplay.blit(self.bgImg, (self.bg_x2, self.bg_y2))

        self.bg_y1 += self.bg_speed
        self.bg_y2 += self.bg_speed

        if self.bg_y1 >= self.display_height:
            self.bg_y1 = -600

        if self.bg_y2 >= self.display_height:
            self.bg_y2 = -600

    def run_enemy_rock(self, thingx, thingy):
        self.gameDisplay.blit(self.enemy_rock, (thingx, thingy))

    def highscore(self, count):
        font = pygame.font.SysFont("arial", 20)
        text = font.render("Score : " + str(count), True, self.white)
        self.gameDisplay.blit(text, (0, 0))

    def display_credit(self):
        font = pygame.font.SysFont("lucidaconsole", 14)
        text = font.render("Thanks for playing!", True, self.white)
        self.gameDisplay.blit(text, (600, 520))


if __name__ == '__main__':
    car_racing = CarRacing()
    car_racing.racing_window()

    car_racing.consumer.start_consuming(car_racing.event_exchange)
    car_racing.consumer.start_consuming(car_racing.chat_exchange)
