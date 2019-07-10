import random


class TreatmentFurnace:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'treatment_furnace_' + str(num + 1)
        self.capacity = 300

        self.current_job_list = []
        print(self.name + ' :: created')

    def calc_treatment_time(self):
        print(self.name, ' :: calculate treatment time')
        return random.randint(30, 50)

    def run(self):
        while True:
            new_job_list = self.alloc.get_next_treatment_job(self.name, self.capacity)
            if new_job_list == None:
                yield self.env.timeout(10)
                continue
            # new_job['properties']['last_process'] = 'treatment_waiting'
            self.current_job_list.extend(new_job_list)
            print('debug :', self.name, self.current_job_list)

            print(self.env.now, self.name, ':: treatment start', self.current_job_list)
            treatment_time = self.calc_treatment_time()
            for j in self.current_job_list:
                # j['properties']['current_equip'] = self.name
                # j['properties']['last_process'] = 'treatment'
                j['properties']['last_process_end_time'] = self.env.now + treatment_time
            yield self.env.timeout(treatment_time)
            for j in self.current_job_list:
                self.alloc.end_job(j)
                # j['properties']['next_instruction'] += 1
                # if len(j['properties']['instruction_list'][0]) == j['properties']['next_instruction']:
                #     j['properties']['state'] = 'done'
                #     #j['properties']['instruction_log'].append(self.name)
            print(self.env.now, self.name, ':: treatment end', self.current_job_list)

            self.current_job_list = []
