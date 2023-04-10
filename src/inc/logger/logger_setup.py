import logging, os

def logger_setup(plm_path, data):
    # TO DO - Instead of try except, just check if full path exists
    # TEST - Logger path not starting with "/"
    try:
        handler = logging.FileHandler(plm_path+data['path'], mode='a')
    except:
        dir = os.path.dirname(data['path'])
        os.makedirs(plm_path+dir)
        handler = logging.FileHandler(plm_path+data['path'], mode='a')
    
    formatter = logging.Formatter('%(asctime)s | %(name)s | %(funcName)s | %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    logger = logging.getLogger(data['name'])
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    return logger