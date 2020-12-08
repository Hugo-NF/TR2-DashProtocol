# MEMBROS DO GRUPO                  MATRÍCULA

# CLARA SENRA RABELLO               16/0025737
# HUGO NASCIMENTO FONSECA           16/0008166
# JOÃO ANSELMO BANDEIRA DOS REIS    16/0031672

import math

import numpy

from player.parser import *
from r2a.ir2a import IR2A
import time


class R2A(IR2A):

    def __init__(self, id):
        IR2A.__init__(self, id)
        self.request_time = 0
        self.qi = []
        self.bandwidths = []
        self.parsed_mpd = ''
        self.current_qi = 0
        self.current_buffer = 0
        self.last_buffer = 0

    def handle_xml_request(self, msg):
        self.request_time = time.perf_counter()
        self.send_down(msg)

    def handle_xml_response(self, msg):
        self.parsed_mpd = parse_mpd(msg.get_payload())
        self.qi = self.parsed_mpd.get_qi()

        # inicialmente, preenchemos o vetor de qualidades de rede com o throughput da resposta ao pedido do xml
        t = time.perf_counter() - self.request_time
        bps = msg.get_bit_length() / t
        for i in range(5):
            self.bandwidths.append(bps)

        self.current_qi = self.bandwidths[-1]
        self.send_up(msg)

    def handle_segment_size_request(self, msg):
        self.request_time = time.perf_counter()

        # calculamos a média ponderada das últimas 5 qualidades de rede, com peso maior para a última medida
        mean_bandwidth = numpy.average(self.bandwidths[-5:], weights=[1, 2, 3, 4, 5])

        # quantizamos a média da qualidade de rede e a última qualidade de rede escolhida
        last_throughput = self.qi[0]
        measured_throughput = self.qi[0]
        max_throughput = self.qi[0]
        for i in self.qi:
            if self.bandwidths[-1] * 0.7 > i:
                measured_throughput = i                         # última qualidade de rede medida
            if self.current_qi > i:
                last_throughput = i                             # última qualidade de rede requisitada
            if mean_bandwidth > i:
                max_throughput = i                              # qualidade média dos últimos 5 throughputs da rede

        k5 = 1.2
        measured_index = self.qi.index(measured_throughput)     # índice da última qualidade de rede medida
        last_index = self.qi.index(last_throughput)             # índice da última qualidade de rede requisitada
        max_index = self.qi.index(max_throughput) * k5          # índice da qualidade média dos últimos 5 throughputs

        self.current_buffer = self.whiteboard.get_amount_video_to_play()
        diff_buffer = self.current_buffer - self.last_buffer

        k1 = 0.75
        k2 = 1.2
        k3 = 0.35
        min_buffer = 7

        k4 = (measured_index - last_index) * k1 + diff_buffer * k2 + (self.current_buffer - min_buffer) * k3

        # baseando-se no padrão AIMD (additive increase, multiplicative decrease), foram definidas diferentes
        # constantes para subtração ou adição ao QI
        if k4 < 0:
            res = last_index + k4 * 0.8
        else:
            res = last_index + k4 * 0.15

        # limitação do índice entre 0 e max_throughput
        bounded_res = max(0, min(int(math.floor(res)), int(math.floor(max_index)), 19))
        self.current_qi = self.qi[bounded_res]

        msg.add_quality_id(self.current_qi)
        self.send_down(msg)

    def handle_segment_size_response(self, msg):
        t = time.perf_counter() - self.request_time
        bps = msg.get_bit_length() / t
        self.bandwidths.append(bps)
        self.last_buffer = self.whiteboard.get_amount_video_to_play()
        self.send_up(msg)

    def initialize(self):
        pass

    def finalization(self):
        pass
