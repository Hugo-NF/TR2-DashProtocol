import math

import numpy

from player.parser import *
from r2a.ir2a import IR2A
import time
from statistics import mean


class R2A(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.request_time = 0
        self.qi = []
        self.response_times = []
        self.bandwidths = []            # vetor de qualidades de rede
        self.parsed_mpd = ''
        self.current_qi = 0             # qualidade escolhida atual
        self.current_buffer = 0
        self.last_buffer = 0

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        t = time.perf_counter() - self.request_time
        self.response_times.append(t)
        self.bandwidths.append(msg.get_bit_length() / t)

        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()
        mean_bandwidth = mean(self.bandwidths[-5:])         # média das últimas 10 qualidades de rede

        # para quantizar a média da qualidade de rede e a última qualidade de rede escolhida
        last_throughput = self.qi[0]
        measured_throughput = self.qi[0]
        max_throughput = self.qi[0]
        for i in self.qi:
            if self.bandwidths[-1] * 0.7 > i:
                measured_throughput = i                         # qualidade correspondente à média da qualidade de rede
            if self.current_qi > i:
                last_throughput = i                             # qualidade correspondente à última qualidade escolhida
            if mean_bandwidth > i:
                max_throughput = i

        k5 = 1.3
        max_index = self.qi.index(max_throughput) * k5
        last_index = self.qi.index(last_throughput)             # índice da última qualidade requisitada
        measured_index = self.qi.index(measured_throughput)     # índice da qualidade do último throughput (rede)
        self.current_buffer = self.whiteboard.get_amount_video_to_play()
        diff_buffer = self.current_buffer - self.last_buffer

        k1 = 0.75
        k2 = 1.2
        k3 = 0.3
        min_buffer = 7

        k4 = (measured_index - last_index) * k1 + diff_buffer * k2 + (self.current_buffer - min_buffer) * k3
        if k4 < 0:
            res = last_index + k4 * 0.8
        else:
            res = last_index + k4 * 0.15                        # aumentar este valor (0.15) aumenta muito a qualidade

        print('>>>>>>>>>>>>>>>>>')
        print(f"mean bandwidth: {mean_bandwidth}")
        print(f"diff buffer: {diff_buffer}")
        print(f"last buffer size: {self.last_buffer}")
        print(f"current buffer size: {self.current_buffer}")
        print(f"result: {res}")
        print('>>>>>>>>>>>>>>>>>')

        bounded_res = max(0, min(int(math.floor(res)), int(math.floor(max_index)), 19))
        self.current_qi = self.qi[bounded_res]
        msg.add_quality_id(self.current_qi)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        self.response_times.append(t)
        bps = msg.get_bit_length() / t
        self.bandwidths.append(bps)
        self.last_buffer = self.whiteboard.get_amount_video_to_play()

        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
