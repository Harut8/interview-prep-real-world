1. create task has bug with mutable default argument so we need to use None and create empty dict inside
2. get_next_task has no lock, but we do not need it since we have only one worker, but in case of multiple workers we need to add lock (RLock)
3. use everywhere Enums
4. for priority we should add it as enum to Task then in task list we should use heap queue to get next task based on priroity otherwise we need to sort list then ack