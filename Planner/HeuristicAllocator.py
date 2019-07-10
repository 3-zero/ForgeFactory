from Equipment.HeatingFurnace import *

class HeuristicAllocator:
    def __init__(self, env, predictor, heating_furnace_num):
        self.env = env
        self.predictor = predictor
        self.heating_furnace_num = heating_furnace_num
        self.insertion = self.env.event()
        self.request = self.env.event()

        self.discharging_wakeup = []
        for i in range(heating_furnace_num):
            self.discharging_wakeup.append(simpy.Store(self.env))
        self.waiting_job = []

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

    def heating_allocate(self, name):
        #아무거나 두개 할당해주게 함

        heating_job_list = []
        for j in self.job:
            if j['properties']['state'] == 'done':
                continue
            if j['properties']['instruction_list'][0][j['properties']['next_instruction']] == 'heating':
                heating_job_list.append(j)
        if len(heating_job_list) == 0:
            return None

        #heating_job_list[0]['properties']['next_instruction'] += 1
        return [heating_job_list[0]]

    def reheating(self, name, job):
        HeatingFurnace.reheating_wakeup.put(name, job)

    def get_next_press_job(self):
        holding_job = self.next_job_list('forging')
        #print('hj :', holding_job)
        if len(holding_job) == 0:
            return None
        target_job = holding_job[0]
        #print('press target job :', target_job)
        for i in range(self.heating_furnace_num):
            #print('target job :', target_job['properties']['instruction_log'][target_job['properties']['next_instruction'] - 1])
            #self.discharging_wakeup[i].put([target_job['properties']['current_equip'], target_job])
            self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
            #self.discharging_wakeup[i].put([target_job['properties']['instruction_log'][target_job['properties']['next_instruction'] - 1], target_job])
        return target_job

    def get_next_cut_job(self):
        holding_job = self.next_job_list('cutting')
        if len(holding_job) == 0:
            return None
        target_job = holding_job[0]
        for i in range(self.heating_furnace_num):
            #self.discharging_wakeup[i].put([target_job['properties']['current_equip'], target_job])
            self.discharging_wakeup[i].put([target_job['properties']['last_heating_furnace'], target_job])
            #self.discharging_wakeup[i].put([target_job['properties']['instruction_log'][target_job['properties']['next_instruction'] - 1], target_job])
        return target_job

    def end_job(self, job):
        self.waiting_job.append(job)

    def get_next_treatment_job(self):
        target_job_list = []
        for j in self.job:
            if j['properties']['state'] == 'done':
                continue
            if j['properties']['last_process_end_time'] != None and j['properties']['last_process_end_time'] > self.env.now:
                continue
            #print('debug', j)
            #print('debug', j['properties']['instruction_list'][0])
            #print('debug', j['properties']['next_instruction'])

            #if len(j['properties']['instruction_list'][0]) == j['properties']['next_instruction']:

            if j['properties']['instruction_list'][0][j['properties']['next_instruction']] == 'treating':
                target_job_list.append(j)

        if len(target_job_list) == 0:
            return None

        for i in range(self.heating_furnace_num):
            self.discharging_wakeup[i].put([target_job_list[0]['properties']['current_equip'], target_job_list[0]])
        return target_job_list[0]