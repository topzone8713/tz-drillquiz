"""
WebSocket Consumer for OpenAI Realtime API Proxy
"""
import json
import logging
import websocket
import threading
import asyncio
from urllib.parse import quote
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class RealtimeProxyConsumer(AsyncWebsocketConsumer):
    """OpenAI Realtime API WebSocket 프록시 Consumer"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.openai_ws = None
        self.openai_thread = None
        self.session_id = None
        self.client_secret = None
        self.loop = None
        self.openai_connected = False  # OpenAI WebSocket 연결 상태
        self.message_queue = []  # 연결 전 메시지 큐
    
    async def connect(self):
        """클라이언트 연결 처리"""
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.loop = asyncio.get_event_loop()
        
        # 세션 정보 가져오기
        session_key = f"realtime_session_{self.session_id}"
        session_data = cache.get(session_key)
        
        if not session_data:
            logger.error(f"세션을 찾을 수 없습니다: {self.session_id}")
            await self.close()
            return
        
        self.client_secret = session_data.get('client_secret')
        if not self.client_secret:
            logger.error(f"client_secret을 찾을 수 없습니다: {self.session_id}")
            await self.close()
            return
        
        # OpenAI API 키 확인
        if not hasattr(settings, 'OPENAI_API_KEY') or not settings.OPENAI_API_KEY:
            logger.error("OpenAI API 키가 설정되지 않았습니다.")
            await self.close()
            return
        
        # WebSocket 연결 수락
        await self.accept()
        
        # OpenAI Realtime API로 프록시 연결
        await self.connect_to_openai()
    
    async def disconnect(self, close_code):
        """클라이언트 연결 종료 처리"""
        logger.info(f"WebSocket 연결 종료 시작: {self.session_id}, close_code={close_code}")
        if self.openai_ws:
            try:
                self.openai_ws.close()
            except Exception as e:
                logger.error(f"OpenAI WebSocket 종료 오류: {e}")
        if self.openai_thread and self.openai_thread.is_alive():
            self.openai_thread.join(timeout=2)
        logger.info(f"WebSocket 연결 종료 완료: {self.session_id}")
    
    async def receive(self, text_data):
        """클라이언트로부터 메시지 수신"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', 'unknown')
            logger.debug(f"클라이언트로부터 메시지 수신: {message_type}")
            
            # 중요한 메시지 타입은 항상 로깅
            if message_type in ['response.create', 'session.update', 'input_audio_buffer.commit']:
                logger.info(f"🔵 [Client→OpenAI] 메시지 전송: {message_type}")
                if message_type == 'response.create':
                    logger.info(f"🔵 [Client→OpenAI] AI 응답 생성 요청!")
            
            # OpenAI WebSocket 연결이 완료되었는지 확인
            if self.openai_connected and self.openai_ws:
                try:
                    self.openai_ws.send(text_data)
                    logger.debug(f"메시지 전송 성공: {message_type}")
                except Exception as send_error:
                    logger.error(f"메시지 전송 오류: {send_error}")
                    # 연결이 끊어진 경우 큐에 추가
                    if "closed" in str(send_error).lower():
                        self.message_queue.append(text_data)
                        logger.info(f"메시지를 큐에 추가 (연결 끊김): {message_type}")
            else:
                # 연결이 완료되지 않았으면 큐에 저장
                self.message_queue.append(text_data)
                logger.debug(f"메시지를 큐에 추가 (연결 대기 중): {message_type}, 큐 크기: {len(self.message_queue)}")
        except Exception as e:
            logger.error(f"메시지 처리 오류: {e}", exc_info=True)
    
    async def connect_to_openai(self):
        """OpenAI Realtime API에 연결"""
        try:
            # WebSocket URL 생성
            encoded_secret = quote(self.client_secret, safe='-_')
            openai_url = f"wss://api.openai.com/v1/realtime?session_id={self.session_id}&client_secret={encoded_secret}&model={settings.OPENAI_MODEL}"
            
            logger.info(f"OpenAI Realtime API 연결 시작: {self.session_id}")
            
            # WebSocket 연결 (동기 함수이므로 별도 스레드에서 실행)
            self.openai_thread = threading.Thread(
                target=self._connect_openai_ws,
                args=(openai_url,),
                daemon=True
            )
            self.openai_thread.start()
            
        except Exception as e:
            logger.error(f"OpenAI 연결 오류: {e}", exc_info=True)
            await self.close()
    
    def _connect_openai_ws(self, url):
        """OpenAI WebSocket 연결 (동기 함수)"""
        try:
            # Authorization 헤더 추가
            headers = [f"Authorization: Bearer {settings.OPENAI_API_KEY}"]
            
            def on_message(ws, message):
                """OpenAI로부터 메시지 수신"""
                try:
                    # 메시지 타입 확인 및 로깅
                    try:
                        message_data = json.loads(message)
                        message_type = message_data.get('type', 'unknown')
                        
                        # 모든 메시지 타입 로깅 (디버깅용)
                        logger.info(f"🔵 [OpenAI→Client] 메시지 수신: {message_type}")
                        
                        # 중요한 메시지 타입 상세 로깅
                        if message_type == 'response.created':
                            logger.info(f"🔵 [OpenAI→Client] AI 응답 생성 시작!")
                        elif message_type == 'response.output_audio.delta':
                            delta_length = len(message_data.get('delta', '')) if message_data.get('delta') else 0
                            logger.info(f"🔵 [OpenAI→Client] AI 오디오 데이터 수신: {delta_length} bytes")
                        elif message_type == 'response.output_item.delta':
                            item_type = message_data.get('item', {}).get('type', 'unknown')
                            if item_type == 'audio_transcript':
                                transcript_delta = message_data.get('item', {}).get('transcript', '')
                                logger.info(f"🔵 [OpenAI→Client] AI 텍스트 전사 델타: {len(transcript_delta)} chars - {transcript_delta[:50]}")
                            else:
                                logger.info(f"🔵 [OpenAI→Client] response.output_item.delta: {item_type}")
                        elif message_type == 'response.output_item.done':
                            item_type = message_data.get('item', {}).get('type', 'unknown')
                            logger.info(f"🔵 [OpenAI→Client] response.output_item.done: {item_type}")
                        elif message_type == 'response.done':
                            logger.info(f"🔵 [OpenAI→Client] AI 응답 완료!")
                            # response.done에 포함된 response 객체 확인
                            if 'response' in message_data:
                                response_obj = message_data['response']
                                status = response_obj.get('status', 'unknown')
                                logger.info(f"🔵 [OpenAI→Client] response.done status: {status}")
                                
                                # 실패한 경우 오류 정보 로깅
                                if status == 'failed':
                                    status_details = response_obj.get('status_details', {})
                                    error_info = status_details.get('error', {})
                                    error_type = error_info.get('type', 'unknown')
                                    error_code = error_info.get('code', 'unknown')
                                    error_message = error_info.get('message', 'No error message')
                                    logger.error(f"❌❌❌ [OpenAI→Client] response.done 실패! ❌❌❌")
                                    logger.error(f"❌ [OpenAI→Client] 오류 타입: {error_type}")
                                    logger.error(f"❌ [OpenAI→Client] 오류 코드: {error_code}")
                                    logger.error(f"❌ [OpenAI→Client] 오류 메시지: {error_message}")
                                
                                # output_items 확인
                                if 'output' in response_obj:
                                    output_items = response_obj.get('output', [])
                                    logger.info(f"🔵 [OpenAI→Client] response.done output_items 수: {len(output_items)}")
                                    for item in output_items:
                                        logger.info(f"🔵 [OpenAI→Client] output_item: {item.get('type', 'unknown')}")
                        elif message_type == 'error':
                            logger.error(f"❌ [OpenAI→Client] 에러 수신: {message_data.get('error', {})}")
                        elif message_type not in ['conversation.item.added', 'conversation.item.done']:
                            # 알 수 없는 메시지 타입은 전체 내용 로깅
                            logger.debug(f"🔵 [OpenAI→Client] 메시지 전체: {json.dumps(message_data, ensure_ascii=False)[:200]}")
                    except Exception as parse_error:
                        logger.warning(f"JSON 파싱 실패: {parse_error}, 원본 메시지: {message[:200]}")
                    
                    # 비동기로 클라이언트에 전달 (기존 이벤트 루프 사용)
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.send(text_data=message),
                            self.loop
                        )
                    else:
                        # 이벤트 루프가 없으면 새로 생성
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.send(text_data=message))
                        loop.close()
                except Exception as e:
                    logger.error(f"메시지 전달 오류: {e}", exc_info=True)
            
            def on_error(ws, error):
                """OpenAI 연결 오류"""
                logger.error(f"OpenAI WebSocket 오류: {error}")
                self.openai_connected = False
                try:
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.close(),
                            self.loop
                        )
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.close())
                        loop.close()
                except Exception as e:
                    logger.error(f"연결 종료 오류: {e}")
            
            def on_close(ws, close_status_code, close_msg):
                """OpenAI 연결 종료"""
                logger.info(f"OpenAI WebSocket 연결 종료: {close_status_code} - {close_msg}")
                self.openai_connected = False
                try:
                    if self.loop and self.loop.is_running():
                        asyncio.run_coroutine_threadsafe(
                            self.close(),
                            self.loop
                        )
                    else:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        loop.run_until_complete(self.close())
                        loop.close()
                except Exception as e:
                    logger.error(f"연결 종료 오류: {e}")
            
            def on_open(ws):
                """OpenAI 연결 성공"""
                logger.info(f"OpenAI WebSocket 연결 성공: {self.session_id}")
                # 연결 상태 업데이트
                self.openai_connected = True
                
                # 큐에 저장된 메시지 전송
                if self.message_queue:
                    logger.info(f"큐에 저장된 메시지 전송 시작: {len(self.message_queue)}개")
                    for queued_message in self.message_queue:
                        try:
                            ws.send(queued_message)
                            logger.debug(f"큐 메시지 전송 성공")
                        except Exception as e:
                            logger.error(f"큐 메시지 전송 실패: {e}")
                    self.message_queue.clear()
                    logger.info("큐 메시지 전송 완료")
            
            # WebSocket 연결
            self.openai_ws = websocket.WebSocketApp(
                url,
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
                on_open=on_open,
                header=headers
            )
            
            # WebSocket 실행 (블로킹)
            self.openai_ws.run_forever()
            
        except Exception as e:
            logger.error(f"OpenAI WebSocket 연결 오류: {e}", exc_info=True)
            try:
                if self.loop and self.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.close(),
                        self.loop
                    )
                else:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(self.close())
                    loop.close()
            except Exception as close_error:
                logger.error(f"연결 종료 오류: {close_error}")

