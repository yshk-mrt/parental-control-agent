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
        NSApplicationActivationPolicyRegular, NSTextAlignmentCenter,
        NSApp, NSRunLoop, NSDefaultRunLoopMode, NSDate, NSTimer
    )
    from Quartz import CGShieldingWindowLevel
    from Foundation import NSMakeRect, NSObject
    
    COCOA_AVAILABLE = True
except ImportError:
    COCOA_AVAILABLE = False
    print("❌ Cocoa dependencies not available")
    sys.exit(1)

class LockScreenView(NSView):
    """ロックスクリーン用のカスタムビュー"""
    
    def initWithFrame_reason_timeout_(self, frame, reason, timeout):
        self = self.initWithFrame_(frame)
        if self:
            self.reason = reason
            self.timeout = timeout
            self.start_time = time.time()
            self.setup_ui()
        return self
    
    def setup_ui(self):
        """UI要素を設定"""
        # 背景色
        self.setWantsLayer_(True)
        self.layer().setBackgroundColor_(NSColor.colorWithRed_green_blue_alpha_(0.1, 0.1, 0.1, 0.95).CGColor())
        
        screen_frame = self.frame()
        
        # ロックアイコン
        lock_icon = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 100, 100))
        lock_icon.setStringValue_("🔒")
        lock_icon.setFont_(NSFont.systemFontOfSize_(72))
        lock_icon.setTextColor_(NSColor.colorWithRed_green_blue_alpha_(1.0, 0.27, 0.27, 1.0))
        lock_icon.setBackgroundColor_(NSColor.clearColor())
        lock_icon.setBordered_(False)
        lock_icon.setEditable_(False)
        lock_icon.setSelectable_(False)
        lock_icon.setAlignment_(NSTextAlignmentCenter)
        
        # アイコンの位置
        lock_x = (screen_frame.size.width - 100) / 2
        lock_y = screen_frame.size.height * 0.6
        lock_icon.setFrame_(NSMakeRect(lock_x, lock_y, 100, 100))
        self.addSubview_(lock_icon)
        
        # タイトル
        title = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 40))
        title.setStringValue_("システムがロックされました")
        title.setFont_(NSFont.boldSystemFontOfSize_(24))
        title.setTextColor_(NSColor.whiteColor())
        title.setBackgroundColor_(NSColor.clearColor())
        title.setBordered_(False)
        title.setEditable_(False)
        title.setSelectable_(False)
        title.setAlignment_(NSTextAlignmentCenter)
        
        title_x = (screen_frame.size.width - 600) / 2
        title_y = lock_y - 60
        title.setFrame_(NSMakeRect(title_x, title_y, 600, 40))
        self.addSubview_(title)
        
        # 理由
        reason_text = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 800, 60))
        reason_text.setStringValue_(self.reason)
        reason_text.setFont_(NSFont.systemFontOfSize_(16))
        reason_text.setTextColor_(NSColor.whiteColor())
        reason_text.setBackgroundColor_(NSColor.clearColor())
        reason_text.setBordered_(False)
        reason_text.setEditable_(False)
        reason_text.setSelectable_(False)
        reason_text.setAlignment_(NSTextAlignmentCenter)
        
        reason_x = (screen_frame.size.width - 800) / 2
        reason_y = title_y - 80
        reason_text.setFrame_(NSMakeRect(reason_x, reason_y, 800, 60))
        self.addSubview_(reason_text)
        
        # ステータス
        self.status_text = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 30))
        self.status_text.setStringValue_("親の承認を待っています...")
        self.status_text.setFont_(NSFont.systemFontOfSize_(16))
        self.status_text.setTextColor_(NSColor.whiteColor())
        self.status_text.setBackgroundColor_(NSColor.clearColor())
        self.status_text.setBordered_(False)
        self.status_text.setEditable_(False)
        self.status_text.setSelectable_(False)
        self.status_text.setAlignment_(NSTextAlignmentCenter)
        
        status_x = (screen_frame.size.width - 600) / 2
        status_y = reason_y - 50
        self.status_text.setFrame_(NSMakeRect(status_x, status_y, 600, 30))
        self.addSubview_(self.status_text)
        
        # 指示
        instructions = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 40))
        instructions.setStringValue_("親に通知が送信されました。\n承認をお待ちください。")
        instructions.setFont_(NSFont.systemFontOfSize_(12))
        instructions.setTextColor_(NSColor.whiteColor())
        instructions.setBackgroundColor_(NSColor.clearColor())
        instructions.setBordered_(False)
        instructions.setEditable_(False)
        instructions.setSelectable_(False)
        instructions.setAlignment_(NSTextAlignmentCenter)
        
        instr_x = (screen_frame.size.width - 600) / 2
        instr_y = status_y - 60
        instructions.setFrame_(NSMakeRect(instr_x, instr_y, 600, 40))
        self.addSubview_(instructions)
        
        # フッター
        footer = NSTextField.alloc().initWithFrame_(NSMakeRect(0, 0, 600, 20))
        footer.setStringValue_("Safe Browser AI - ペアレンタルコントロールシステム")
        footer.setFont_(NSFont.systemFontOfSize_(12))
        footer.setTextColor_(NSColor.whiteColor())
        footer.setBackgroundColor_(NSColor.clearColor())
        footer.setBordered_(False)
        footer.setEditable_(False)
        footer.setSelectable_(False)
        footer.setAlignment_(NSTextAlignmentCenter)
        
        footer_x = (screen_frame.size.width - 600) / 2
        footer_y = 40
        footer.setFrame_(NSMakeRect(footer_x, footer_y, 600, 20))
        self.addSubview_(footer)
    
    def update_status(self, remaining_time):
        """ステータスを更新"""
        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            status = f"親の承認を待っています... ({minutes:02d}:{seconds:02d})"
        else:
            status = "リクエストがタイムアウトしました"
        
        self.status_text.setStringValue_(status)

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
        self.monitor_thread = threading.Thread(target=self._monitor_signals, daemon=True)
        self.monitor_thread.start()
        print("🔍 シグナル監視スレッドを開始しました")
        
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
    parser.add_argument('--reason', default='不適切なコンテンツが検出されました', help='ロックの理由')
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