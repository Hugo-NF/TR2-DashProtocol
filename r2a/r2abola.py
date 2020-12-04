from player.parser import *
from r2a.ir2a import IR2A
import time


class R2ABola(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.request_time = 0
        self.qi = []
        self.current_qi = 0
        self.parsed_mpd = ''
        self.current_seconds_on_buffer = 0
        self.new_seconds_on_buffer = 0
        self.throughput = 0

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        self.throughput = msg.get_bit_length() / t
        print(f"first throughput: {self.throughput}")

        self.current_qi = self.qi[0]
        for i in self.qi:
            if self.throughput > i:
                self.current_qi = i

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        diff_buffer = self.new_seconds_on_buffer - self.current_seconds_on_buffer

        index = self.qi.index(self.current_qi)

        print(">>>>>>>>>")
        print(index)
        print(self.new_seconds_on_buffer)
        print(self.current_seconds_on_buffer)
        print(">>>>>>>>>")

        if self.new_seconds_on_buffer > 20:
            index += 2
        if self.new_seconds_on_buffer > 15:
            print('entrou > 10')
            if diff_buffer == 0:                    # aumenta normal
                index += 1
            elif diff_buffer > 0:                   # aumenta muito
                index += 2
            elif diff_buffer < 0:                   # diminui muito
                index -= 1
            elif diff_buffer < -5:                  # diminui muito mesmo
                index -= 3
        else:
            print('entrou < 10')
            if diff_buffer == 0:                    # mantém
                index += 0
            elif diff_buffer > 0:                   # aumenta um pouquinho
                index += 1
            elif diff_buffer < 0:                   # diminui muito
                index -= 2
            elif diff_buffer < -4:                  # diminui muito mesmo
                index -= 3

        index = max(0, min(index, 19))
        throughput_qi = self.qi[0]
        for i in self.qi:
            if self.throughput > i:
                throughput_qi = i
        if throughput_qi < 0.5 * self.qi[index]:
            index = self.qi.index(throughput_qi)

        print(f"CURRENT QI: {index}")
        index = max(0, min(index, 19))
        # print(f"selected qi: {self.current_qi}")

        self.current_qi = self.qi[index]
        msg.add_quality_id(self.current_qi)

        self.current_seconds_on_buffer = self.whiteboard.get_amount_video_to_play()
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        self.throughput = msg.get_bit_length() / t
        self.new_seconds_on_buffer = self.whiteboard.get_amount_video_to_play()
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
