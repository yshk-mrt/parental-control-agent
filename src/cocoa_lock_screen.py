#!/usr/bin/env python3
"""
独立したCocoaロックスクリーンアプリケーション

このスクリプトは、独立したプロセスとして実行され、
macOSのフォアグラウンドアプリケーションとして動作します。
"""

import sys
import time
import os
import argparse
import threading
from datetime import datetime

# Cocoaフレームワークをインポート
try:
    from Cocoa import (
        NSApplication, NSWindow, NSScreen, NSColor, NSView, NSTextField, NSFont,
        NSBackingStoreBuffered, NSWindowStyleMaskBorderless,
        NSApplicationActivationPolicyRegular, NSTextAlignmentCenter, NSTextAlignmentLeft,
        NSApp, NSRunLoop, NSDefaultRunLoopMode, NSDate, NSTimer, NSImageView, NSImage,
        NSViewWidthSizable, NSViewHeightSizable, NSImageScaleProportionallyUpOrDown,
        NSBezierPath
    )
    from Quartz import CGShieldingWindowLevel
    from Foundation import NSMakeRect, NSObject
    
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("❌ Cocoa dependencies not available")
    sys.exit(1)

class SpeechBubbleView(NSView):
    """Speech bubble view for displaying messages"""
    
    def initWithFrame_message_(self, frame, message):
        self = self.initWithFrame_(frame)
        if self:
            self.message = message
            self.setup_ui()
        return self
    
    def setup_ui(self):
        """Setup UI components for speech bubble"""
        # Create message text field
        self.message_label = NSTextField.alloc().initWithFrame_(
            NSMakeRect(20, 20, self.frame().size.width - 40, self.frame().size.height - 40)
        )
        self.message_label.setStringValue_(self.message)
        self.message_label.setFont_(NSFont.boldSystemFontOfSize_(24))  # 大きな文字
        self.message_label.setTextColor_(NSColor.blackColor())
        self.message_label.setBackgroundColor_(NSColor.clearColor())
        self.message_label.setBezeled_(False)
        self.message_label.setEditable_(False)
        self.message_label.setSelectable_(False)
        self.message_label.setAlignment_(NSTextAlignmentLeft)
        self.message_label.cell().setWraps_(True)
        self.addSubview_(self.message_label)
    
    def drawRect_(self, rect):
        """Draw the speech bubble background"""
        # Set bubble background color (solid white)
        bubble_color = NSColor.whiteColor()
        bubble_color.set()
        
        # Create rounded rectangle for speech bubble
        bubble_rect = NSMakeRect(10, 10, rect.size.width - 20, rect.size.height - 20)
        bubble_path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(bubble_rect, 15, 15)
        bubble_path.fill()
        
        # Draw border
        border_color = NSColor.colorWithRed_green_blue_alpha_(0.8, 0.8, 0.8, 1.0)
        border_color.set()
        bubble_path.setLineWidth_(2)
        bubble_path.stroke()
    
    def update_message(self, message):
        """Update the message in the speech bubble"""
        self.message = message
        if self.message_label:
            self.message_label.setStringValue_(message)

class LockScreenView(NSView):
    """ロックスクリーンのカスタムビュー"""
    
    def initWithFrame_reason_timeout_(self, frame, reason, timeout):
        self = self.initWithFrame_(frame)
        if self:
            self.reason = reason
            self.timeout = timeout
            self.setup_ui()
        return self
    
    def setup_ui(self):
        """UIコンポーネントを設定"""
        # 背景画像を設定
        self.setup_background_image()
        
        # 画面の中央に配置するためのフレーム計算
        screen_frame = self.frame()
        center_x = screen_frame.size.width / 2
        center_y = screen_frame.size.height / 2
        
        # 左上の吹き出しを作成
        bubble_width = 500
        bubble_height = 300
        bubble_x = 100  # 左マージン
        bubble_y = screen_frame.size.height - bubble_height - 100  # 上マージン
        
        initial_message = f"🔒 System Locked!\n\nReason: {self.reason}\n\nWaiting for parental approval...\nA notification has been sent to your parent."
        self.speech_bubble = SpeechBubbleView.alloc().initWithFrame_message_(
            NSMakeRect(bubble_x, bubble_y, bubble_width, bubble_height),
            initial_message
        )
        self.addSubview_(self.speech_bubble)
        
        # 中央のメッセージは削除し、すべて左上の吹き出しに集約
    
    def setup_background_image(self):
        """背景画像を設定"""
        # まず上下を黒色(透過なし)で埋める
        self.setWantsLayer_(True)
        if self.layer():
            self.layer().setBackgroundColor_(NSColor.blackColor().CGColor())
        
        # 背景画像のパスを取得
        current_dir = os.path.dirname(os.path.abspath(__file__))
        image_path = os.path.join(current_dir, "..", "assets", "lock_background.jpg")
        
        if os.path.exists(image_path):
            try:
                # 画像を読み込み
                image = NSImage.alloc().initWithContentsOfFile_(image_path)
                if image:
                    # 画像のサイズを取得
                    image_size = image.size()
                    screen_frame = self.frame()
                    
                    # 画像のアスペクト比を保持して中央に配置
                    aspect_ratio = image_size.width / image_size.height
                    screen_aspect_ratio = screen_frame.size.width / screen_frame.size.height
                    
                    if aspect_ratio > screen_aspect_ratio:
                        # 画像の方が横長の場合、幅を画面に合わせる
                        image_width = screen_frame.size.width
                        image_height = image_width / aspect_ratio
                    else:
                        # 画像の方が縦長の場合、高さを画面に合わせる
                        image_height = screen_frame.size.height
                        image_width = image_height * aspect_ratio
                    
                    # 中央に配置
                    image_x = (screen_frame.size.width - image_width) / 2
                    image_y = (screen_frame.size.height - image_height) / 2
                    
                    # 背景画像ビューを作成
                    background_view = NSImageView.alloc().initWithFrame_(
                        NSMakeRect(image_x, image_y, image_width, image_height)
                    )
                    background_view.setImage_(image)
                    background_view.setImageScaling_(NSImageScaleProportionallyUpOrDown)
                    
                    # 透過なし（元の設定）
                    background_view.setAlphaValue_(1.0)
                    
                    # 背景として追加
                    self.addSubview_(background_view)
                    
                    print(f"✅ 背景画像を設定しました: {image_path}")
                else:
                    print(f"⚠️ 画像の読み込みに失敗しました: {image_path}")
                    self.setup_fallback_background()
            except Exception as e:
                print(f"❌ 背景画像設定エラー: {e}")
                self.setup_fallback_background()
        else:
            print(f"⚠️ 背景画像が見つかりません: {image_path}")
            print("📝 画像を以下のパスに保存してください:")
            print(f"   {image_path}")
            self.setup_fallback_background()
    
    def setup_fallback_background(self):
        """フォールバック背景を設定"""
        # グラデーション背景を作成
        try:
            # 単色の背景色を設定
            self.setWantsLayer_(True)
            if self.layer():
                # 深い青色の背景
                self.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.1, 0.2, 0.4, 0.9).CGColor())
                print("✅ フォールバック背景を設定しました")
        except Exception as e:
            print(f"⚠️ フォールバック背景設定エラー: {e}")
    
    def update_status(self, remaining_time):
        """ステータスを更新"""
        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            bubble_text = f"🔒 System Locked!\n\nReason: {self.reason}\n\nWaiting for parental approval...\nTime remaining: {minutes:02d}:{seconds:02d}\n\nA notification has been sent to your parent."
        else:
            bubble_text = f"🔒 System Locked!\n\nReason: {self.reason}\n\nRequest timed out.\nPlease try again later."
        
        if self.speech_bubble:
            self.speech_bubble.update_message(bubble_text)

class LockScreenApp:
    """ロックスクリーンアプリケーション"""
    
    def __init__(self, reason, timeout):
        self.reason = reason
        self.timeout = timeout
        self.start_time = time.time()
        self.window = None
        self.view = None
        self.timer = None
        self.should_quit = False
        self.monitor_thread = None
        
        # アプリケーションの初期化
        self.app = NSApplication.sharedApplication()
        self.app.setActivationPolicy_(NSApplicationActivationPolicyRegular)
        
    def start_monitoring_thread(self):
        """シグナル監視スレッドを開始"""
        # 起動時に古いシグナルファイルをクリーンアップ
        self.cleanup_old_signal_files()
        
        self.monitor_thread = threading.Thread(target=self._monitor_signals, daemon=True)
        self.monitor_thread.start()
        print("🔍 シグナル監視スレッドを開始しました")
    
    def cleanup_old_signal_files(self):
        """古いシグナルファイルをクリーンアップ"""
        signal_files = [
            '/tmp/cocoa_lock_unlock',
            '/tmp/unlock_signal',
            '/tmp/cocoa_overlay_unlock'
        ]
        
        for signal_file in signal_files:
            try:
                if os.path.exists(signal_file):
                    os.remove(signal_file)
                    print(f"🧹 古いシグナルファイルを削除: {signal_file}")
            except Exception as e:
                print(f"⚠️ シグナルファイル削除エラー: {signal_file} - {e}")
        
        print("✅ シグナルファイルクリーンアップ完了")
    
    def _monitor_signals(self):
        """シグナルファイルを監視"""
        signal_file = '/tmp/cocoa_lock_unlock'
        last_check_time = 0
        
        while not self.should_quit:
            try:
                current_time = time.time()
                elapsed = current_time - self.start_time
                
                # タイムアウトチェック
                if elapsed >= self.timeout:
                    print("⏰ タイムアウトしました")
                    self.should_quit = True
                    # メインスレッドでアプリケーションを終了
                    self.app.performSelectorOnMainThread_withObject_waitUntilDone_(
                        'terminate:', None, False
                    )
                    break
                
                # シグナルファイルをチェック
                if os.path.exists(signal_file):
                    print("🔓 解除シグナルを受信しました")
                    try:
                        os.remove(signal_file)
                        print("📁 シグナルファイルを削除しました")
                    except Exception as e:
                        print(f"⚠️ シグナルファイル削除エラー: {e}")
                    
                    self.should_quit = True
                    # メインスレッドでアプリケーションを終了
                    self.app.performSelectorOnMainThread_withObject_waitUntilDone_(
                        'terminate:', None, False
                    )
                    break
                
                # デバッグ用：5秒ごとにステータスを出力
                if int(elapsed) % 5 == 0 and int(elapsed) != last_check_time:
                    remaining = max(0, self.timeout - elapsed)
                    print(f"🔍 監視中... 経過時間: {int(elapsed)}秒, 残り時間: {int(remaining)}秒")
                    print(f"📁 シグナルファイル {signal_file} 存在: {os.path.exists(signal_file)}")
                    last_check_time = int(elapsed)
                
                time.sleep(0.5)  # 0.5秒間隔でチェック
                
            except Exception as e:
                print(f"❌ 監視エラー: {e}")
                time.sleep(1)
    
    def create_window(self):
        """ウィンドウを作成"""
        # メインスクリーンを取得
        screen = NSScreen.mainScreen()
        screen_frame = screen.frame()
        
        # ウィンドウを作成
        self.window = NSWindow.alloc().initWithContentRect_styleMask_backing_defer_(
            screen_frame,
            NSWindowStyleMaskBorderless,
            NSBackingStoreBuffered,
            False
        )
        
        # ウィンドウの設定
        self.window.setLevel_(CGShieldingWindowLevel())
        self.window.setOpaque_(False)
        self.window.setBackgroundColor_(NSColor.clearColor())
        self.window.setIgnoresMouseEvents_(False)
        self.window.setAcceptsMouseMovedEvents_(False)
        
        # カスタムビューを作成
        self.view = LockScreenView.alloc().initWithFrame_reason_timeout_(
            screen_frame, self.reason, self.timeout
        )
        self.window.setContentView_(self.view)
        
        # ウィンドウを表示
        self.window.makeKeyAndOrderFront_(None)
        self.window.orderFrontRegardless()
        
        # アプリケーションをアクティブにする
        self.app.activateIgnoringOtherApps_(True)
        
        print(f"✅ ロックスクリーンが表示されました: {self.reason}")
        
    def update_timer_(self, timer):
        """タイマーの更新（Objective-C用のメソッド名）"""
        elapsed = time.time() - self.start_time
        remaining = max(0, self.timeout - elapsed)
        
        # デバッグ出力を追加
        print(f"⏰ タイマー更新: 経過時間={int(elapsed)}秒, 残り時間={int(remaining)}秒")
        
        if self.view:
            self.view.update_status(remaining)
        
        # タイムアウトチェック
        if remaining <= 0:
            print("⏰ タイムアウトしました")
            self.quit()
        
        # 解除シグナルファイルをチェック
        signal_file = '/tmp/cocoa_lock_unlock'
        if os.path.exists(signal_file):
            print("🔓 解除シグナルを受信しました")
            try:
                os.remove(signal_file)
                print("📁 シグナルファイルを削除しました")
            except Exception as e:
                print(f"⚠️ シグナルファイル削除エラー: {e}")
            self.quit()
        else:
            # デバッグ用：5秒ごとにシグナルファイルをチェック
            if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                print(f"🔍 シグナルファイルをチェック中... (経過時間: {int(elapsed)}秒)")
                print(f"📁 {signal_file} 存在確認: {os.path.exists(signal_file)}")
    
    # 旧メソッド名も残す（互換性のため）
    def update_timer(self, timer):
        """タイマーの更新（旧メソッド名）"""
        return self.update_timer_(timer)
    
    def quit(self):
        """アプリケーションを終了"""
        print("🔓 アプリケーションを終了中...")
        self.should_quit = True
        
        if self.timer:
            self.timer.invalidate()
        if self.window:
            self.window.close()
        
        # 監視スレッドの終了を待つ
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=1)
            
        self.app.terminate_(None)
    
    def run(self):
        """アプリケーションを実行"""
        try:
            # ウィンドウを作成
            self.create_window()
            
            # タイマーを開始
            self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
                0.5, self, 'update_timer_:', None, True
            )
            
            # シグナル監視スレッドを開始
            self.start_monitoring_thread()

            # メインループを開始
            self.app.run()
            
        except KeyboardInterrupt:
            print("\\n🔓 キーボード割り込みで終了")
            self.quit()
        except Exception as e:
            print(f"❌ エラー: {e}")
            import traceback
            traceback.print_exc()

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Cocoaロックスクリーン')
    parser.add_argument('--reason', default='Inappropriate content detected', help='ロックの理由')
    parser.add_argument('--timeout', type=int, default=300, help='タイムアウト時間（秒）')
    
    args = parser.parse_args()
    
    if not COCOA_AVAILABLE:
        print("❌ Cocoa dependencies not available")
        sys.exit(1)
    
    print(f"🔒 ロックスクリーンを開始: {args.reason}")
    print(f"⏰ タイムアウト: {args.timeout}秒")
    
    app = LockScreenApp(args.reason, args.timeout)
    app.run()

if __name__ == "__main__":
    main() 