import random

class Press:
    def __init__(self, env, allocator, num):
        self.env = env
        self.alloc = allocator

        self.name = 'press_' + str(num + 1)

        self.current_job = None
        print(self.name + ' :: created')

    def calc_press_time(self):
        print(self.name, ' :: calculate press time')
        return random.randint(30, 50)

    def run(self):
        while True:
            self.current_job = self.alloc.get_next_press_job()
            if self.current_job == None:
                yield self.env.timeout(10)
                continue
            print(self.env.now, self.name, ':: press start', self.current_job)
            press_time = self.calc_press_time()
            self.current_job['properties']['current_equip'] = self.name
            self.current_job['properties']['last_process'] = 'press'
            self.current_job['properties']['last_process_end_time'] = self.env.now + press_time
            yield self.env.timeout(press_time)
            self.current_job['properties']['next_instruction'] += 1
            if len(self.current_job['properties']['instruction_list'][0]) == self.current_job['properties']['next_instruction']:
                self.current_job['properties']['state'] = 'done'
            print(self.env.now, self.name, ':: press end', self.current_job)
            self.alloc.end_job(self.current_job)
            #self.current_job = None
            #이거 해도 되나?? current job 저장된 본체가 사라지나..? 추후에 테스트 (굳이 안바꿔줘도 상관없긴 함)