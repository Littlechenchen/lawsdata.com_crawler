import os
from multiprocessing.pool import Pool

def printn(n):
    print(os.getpid(), n**2)
    return n**2

if __name__ == '__main__':
    p = Pool(3)
    # for i in range(100000):

    #     p.apply_async(printn, args=(i,))
    #     #ans =  p.map_async(printn, args=(i,) )
    p.map_async(printn, range(1000))

    print('asdc')
    p.close()
    p.join()
    #print('ans:', ans)