import os
import random
import sys
import time
import math

import pygame as pg

WIDTH = 1600  # ゲームウィンドウの幅
HEIGHT = 900  # ゲームウィンドウの高さ
MAIN_DIR = os.path.split(os.path.abspath(__file__))[0]
NUM_OF_BOMBS = 5


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとん，または，爆弾SurfaceのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


class Bird:
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -5),
        pg.K_DOWN: (0, +5),
        pg.K_LEFT: (-5, 0),
        pg.K_RIGHT: (+5, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        """
        img0 = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん（右向き）
        self.imgs = {  # 0度から反時計回りに定義
                    (+5, 0): img,  # 右
                    (+5, -5): pg.transform.rotozoom(img, 45, 1.0),  # 右上
                    (0, -5): pg.transform.rotozoom(img, 90, 1.0),  # 上
                    (-5, -5): pg.transform.rotozoom(img0, -45, 1.0),  # 左上
                    (-5, 0): img0,  # 左
                    (-5, +5): pg.transform.rotozoom(img0, 45, 1.0),  # 左下
                    (0, +5): pg.transform.rotozoom(img, -90, 1.0),  # 下
                    (+5, +5): pg.transform.rotozoom(img, -45, 1.0),  # 右下
                    }
        self.img = pg.transform.flip(  # 左右反転
            pg.transform.rotozoom(  # 2倍に拡大
                pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 
                0, 
                2.0), 
            True, 
            False
        )
        self.rct = self.img.get_rect()
        self.rct.center = xy
        self.dire = (+5,0)

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.img = pg.transform.rotozoom(pg.image.load(f"{MAIN_DIR}/fig/{num}.png"), 0, 2.0)
        screen.blit(self.img, self.rct)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
       
        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        if sum_mv != [0, 0]:
            self.dire = tuple(sum_mv)
        self.rct.move_ip(sum_mv)
        if check_bound(self.rct) != (True, True):
            self.rct.move_ip(-sum_mv[0], -sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.img = self.imgs[tuple(sum_mv)]
        screen.blit(self.img, self.rct)


class Bomb:
    colors = [(255,0,0),[0,255,0],[0,0,255],
              [255,255,0],[255,0,255],[0,255,255]]
    """
    爆弾に関するクラス
    """
    def __init__(self):
        """
        爆弾円Surfaceを生成する
        """
        rad = random.randint(10,100)
        self.img = pg.Surface((2*rad, 2*rad))
        color = random.choice(Bomb.colors)
        pg.draw.circle(self.img, color, (rad, rad), rad)
        self.img.set_colorkey((0, 0, 0))
        self.rct = self.img.get_rect()
        self.rct.center = random.randint(0, WIDTH), random.randint(0, HEIGHT)
        self.vx, self.vy = random.choice([-5,5]),random.choice([-5,5])

    def update(self, screen: pg.Surface):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        yoko, tate = check_bound(self.rct)
        if not yoko:
            self.vx *= -1
        if not tate:
            self.vy *= -1
        self.rct.move_ip(self.vx, self.vy)
        screen.blit(self.img, self.rct)

class Beam:
    def __init__(self,bird:Bird):
        self.img = pg.image.load(f"{MAIN_DIR}/fig/beam.png")
        vx, vy = bird.dire
        theta = math.atan2(-vy, vx) # 直交座標から極座標の角度を計算
        angle = math.degrees(theta)
        self.image2 = pg.transform.rotozoom(self.img, angle, 1)
        self.rct = self.image2.get_rect()
        self.rct.centerx = bird.rct.centerx + bird.rct.width * vx / 5
        self.rct.centery = bird.rct.centery + bird.rct.height * vy / 5
        self.vx = vx
        self.vy = vy

    def update(self,screen:pg.Surface):
        self.rct.move_ip(self.vx,self.vy)
        screen.blit(self.image2,self.rct)

class  Explosion:
    """
    爆発エフェクトに関するクラス
    引数 center: 爆発エフェクトの中心位置を指定
    imagesリスト: 爆発エフェクトに使用される画像のリストを格納する
    """
    def __init__(self, center):
        self.images = [pg.image.load(f"ex03/fig/explosion.gif")] #画像を読み込み
        self.images += [pg.transform.flip(img, True, False) for img in self.images]  # 上下左右にflipしたものを画像リストに格納
        self.index = 0 # index変数は初期値を0としてインデックスを保持する。
        self.image = self.images[self.index] #現在の画像を表示させる。
        self.rct = self.image.get_rect()#爆発エフェクトを表示
        self.rct.center = center #位置を設定
        self.life = 10 #表示時間(10)lifeを設定
    
    def update(self):
        self.life -= 1#爆発経過時間lifeを１減算
        if self.life <= 0: #0より小さい値の場合
            return True  # 爆発が終了したことを示すためにTrueを返す
        if self.index < len(self.images) - 1: #imagesリストの最後のインデックスに達していない場合、indexを更新する
            self.index += 1
        self.image = self.images[self.index]
        return False  # 爆発が続行中であることを示すためにFalseを返す

def main():
    pg.display.set_caption("たたかえ！こうかとん")
    screen = pg.display.set_mode((WIDTH, HEIGHT))    
    bg_img = pg.image.load(f"{MAIN_DIR}/fig/pg_bg.jpg")
    bird = Bird(3, (900, 400))
    # BombインスタンスがNUM個並んだリスト
    bombs = [Bomb() for i in range(NUM_OF_BOMBS)]  
    beam = None
    explosions = []

    clock = pg.time.Clock()
    tmr = 0
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:  # スペースキーが押されたら
                beam = Beam(bird)  # ビームインスタンスの生成
        
        screen.blit(bg_img, [0, 0])
        
        for bomb in bombs:
            if bird.rct.colliderect(bomb.rct):
                # ゲームオーバー時に，こうかとん画像を切り替え，1秒間表示させる
                bird.change_img(8, screen)
                pg.display.update()
                time.sleep(1)
                return

        for i, bomb in enumerate(bombs):
            if beam is not None and beam.rct.colliderect(bomb.rct):
                explosions.append(Explosion(bomb.rct.center))
                beam = None
                bombs[i] = None
                bird.change_img(6, screen)
        # Noneでない爆弾だけのリストを作る
        bombs = [bomb for bomb in bombs if bomb is not None]
        explosions = [explosion for explosion in explosions if not explosion.update()]
        for explosion in explosions:
            screen.blit(explosion.image, explosion.rct)

        key_lst = pg.key.get_pressed()
        bird.update(key_lst, screen)
        for bomb in bombs:
            bomb.update(screen)
        if beam is not None:
            beam.update(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
