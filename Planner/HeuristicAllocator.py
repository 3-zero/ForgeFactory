from Equipment.HeatingFurnace import *
from queue import Queue

class HeuristicAllocator:
    def __init__(self, env, predictor, heating_furnace_num):
        self.env = env
        self.predictor = predictor
        self.heating_furnace_num = heating_furnace_num
        self.insertion = self.env.event()
        self.request = self.env.event()

        self.discharging_wakeup = []
        self.recharging_wakeup = []
        for i in range(heating_furnace_num):
            self.discharging_wakeup.append(simpy.Store(self.env))
            self.recharging_wakeup.append(simpy.Store(self.env))
        self.waiting_job = []
        self.complete_job = []
        self.recharging_queue = []

        self.hf_count = 0
        self.job = None

    def next_job_list(self, process):
        next_job = []
        for job in self.job:
            if job['properties']['last_process'] != 'holding':
                continue
            if job['properties']['state'] == 'done':
                continue
            if (job['properties']['last_process_end_time'] < self.env.now) and (job['properties']['instruction_list'][0][job['properties']['next_instruction']] == process):
                #print('debug2 : ', self.env.now, job)
                next_job.append(job)
        #print('debug : wj :', self.waiting_job)
        for wj in self.waiting_job:
            #구문 remove 필요
            if wj['properties']['state'] == 'done':
                continue
            if wj['properties']['last_process_end_time'] > self.env.now:
                self.waiting_job.remove(wj)
                continue
            if wj['properties']['instruction_list'][0][wj['properties']['next_instruction']] == process:
                next_job.append(wj)
                self.waiting_job.remove(wj)

        #print('debug : nj :', next_job)
        return next_job

    def select_job(self, job_list):
        remained_job_list = []
        selected_job_list = []
        job_list = sorted(job_list, key=lambda j:j['properties']['deadline'])
        urgent_job = job_list[0]
        urgent_job_weight = urgent_job['properties']['ingot']['current_weight']
        deadline = urgent_job['properties']['deadline']
        deadline += 7*24*60 # deadline 간격 7일 이내의 작업들을 가져오기 위한 설정. 보완필요.
        for j in job_list:
            cur_job_deadline = j['properties']['deadline']
            cur_job_weight = j['properties']['ingot']['current_weight']
            if cur_job_deadline < deadline and cur_job_weight == urgent_job_weight:
                selected_job_list.append(j)
            else:
                remained_job_list.append(j)
        return selected_job_list, remained_job_list

    def heating_allocate(self, name, capacity):
        # -----------------------------------------------------------------------
        # 가열로 작업 할당 휴리스틱
        # 1. 마감기한이 가장 이른 작업 하나 선택
        # 2. 마감기한 간격 7일 내 해당 작업과 동일 제품 혹은 동일 무게 작업 선택
        # 3. 가열로 Capacity 85% 이상 채워질 때까지 반복
        # -----------------------------------------------------------------------

        # 후보 작업 목록
        candidate_job_list = []
        for j in self.job:
            if j['properties']['state'] == 'done':
                continue
            last_process_end_time = j['properties']['last_process_end_time']
            try:
                # 예외처리보완필요
                # treating 중인 작업들의 경우 len(j['properties']['instruction_list']) == j['properties']['next_instruction'] 인 경우 발생
                # list index out of range 에러 발생
                next_instruction = j['properties']['instruction_list'][0][j['properties']['next_instruction']]
            except:
                pass
            if last_process_end_time == None and next_instruction == 'heating':
                candidate_job_list.append(j)
            if last_process_end_time != None and last_process_end_time < self.env.now and next_instruction == 'heating':
                candidate_job_list.append(j)
        if len(candidate_job_list) == 0:
            return None

        allocate_job_list = []
        total_weight = 0
        print('debug: ', name, candidate_job_list)
        while total_weight < capacity * 0.85:
            selected_job_list, candidate_job_list = self.select_job(candidate_job_list)
            for j in selected_job_list:
                cur_job_weight = j['properties']['ingot']['current_weight']
                if total_weight + cur_job_weight < capacity:
                    j['properties']['current_equip'] = name
                    j['properties']['last_process'] = 'heating'
                    j['properties']['last_heating_furnace'] = name
                    j['properties']['next_instruction'] += 1
                    allocate_job_list.append(j)
                else:
                    candidate_job_list.append(j)
            if len(candidate_job_list) == 0:
                break
        return allocate_job_list

    def recharging(self, job):
        # ----------------------------------------------------------------------------------------------------
        # 가열로 재장입 작업 할당 휴리스틱
        # 1. 현재 문이 열려있거나 온도 유지 중인 가열로를 찾음
        # 2. 평균 중량이 해당 작업의 중량과 가장 유사한 가열로를 선택
        # 3. 문이 열려있거나 온도 유지 중인 가열로가 없는 경우 생길 때까지 대기
        # ----------------------------------------------------------------------------------------------------
        self.recharging_queue.append(job)
        """
        모든 가열로에 job 건네주며 요청.

        가열로가 열려있거나 온도유지중이라면
            job을 받고 추가 후 reheating 시간 다시 예측.
            allocator의 reheating queue에서 지워줌.

        아니라면
            반복
        """

    def _recharging(self):
        if len(self.recharging_queue) != 0:
            HeatingFurnace.recharging_wakeup[self.hf_count].put(self.recharging_queue[0])
        yield self.env.timeout(1)
        self.hf_count += 1

    # 세영수정
    def get_next_press_job(self):
        candidate_job_list = self.next_job_list('forging')
        if len(candidate_job_list) == 0:
            return None
        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        target_job = candidate_job_list[0]
        if target_job['properties']['last_process'] == 'holding':
            for i in range(self.heating_furnace_num):
                self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
        print(self.env.now, 'press target job :', target_job)
        return target_job

    # 세영수정
    def get_next_cut_job(self):
        candidate_job_list = self.next_job_list('cutting')
        if len(candidate_job_list) == 0:
            return None
        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        target_job = candidate_job_list[0]
        if target_job['properties']['last_process'] == 'holding':
            for i in range(self.heating_furnace_num):
                self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
        print(self.env.now, 'cutter target job :', target_job)
        return target_job

    # 세영수정
    def end_job(self, job):
        if len(job['properties']['instruction_list'][0]) == job['properties']['next_instruction']:
            job['properties']['state'] = 'done'
            self.complete_job.append(job)
        else:
            self.waiting_job.append(job)

    # 세영수정
    def get_next_treatment_job(self, name, capacity):
        # ----------------------------------------------------------------------------------------------------
        # 열처리로 작업 할당 휴리스틱
        # 1. 마감기한이 임박한 순으로 작업 선택
        # 2. 열처리로 Capacity 85% 이상 채워질 때까지 대기
        # 3. 열처리 공정 소요 시간을 예측했을 때 마감기한을 어기는 작업이 생길 경우 더이상 기다리지 않고 할당
        # ----------------------------------------------------------------------------------------------------
        candidate_job_list = []
        for j in self.job:
            if j['properties']['state'] == 'done':
                continue
            if j['properties']['last_process_end_time'] != None and j['properties']['last_process_end_time'] > self.env.now:
                continue
            if j['properties']['instruction_list'][0][j['properties']['next_instruction']] == 'treating':
                candidate_job_list.append(j)

        if len(candidate_job_list) == 0:
            return None
        candidate_job_list = sorted(candidate_job_list, key=lambda j: j['properties']['deadline'])
        target_job_list = []
        filled = 0
        for j in candidate_job_list:
            cur_job_weight = j['properties']['ingot']['current_weight']
            if filled + cur_job_weight < capacity:
                filled += j['properties']['ingot']['current_weight']
                target_job_list.append(j)

        for j in target_job_list:
            j['properties']['current_equip'] = name
            j['properties']['last_process'] = 'treatment'
            j['properties']['next_instruction'] += 1

        return target_job_list