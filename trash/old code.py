
### Old code ###

# Itearate over all files, find the best FE for each file
best_fe_for_file = dict() 
for file_id in range(1,17+1):
    # continue # Skip this part for now.
    filename = 'cdgeb-file-' + str(file_id).zfill(2)
    
    method = 0
    
    match method:
        case 2:
            # Counting the number of "wins" every front-end got from any of the probes.
            score = dict()
            for probe_id in range(1,14+1):
                winner_fe = min(measurements.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # probe_name == probename
                    pair[0][0] == 'cdgeb-probe-' + str(probe_id).zfill(2) and \
                    # and file == filename
                    pair[0][2] == filename \
                    else float('inf'))[0][1]
                
                score[winner_fe] = score[winner_fe] + 1 if winner_fe in score else 1

            best_fe_for_file[filename] = max(score, key=score.get)
    
        case 3:
            # Compare the mean times took for each front-end.
            means = {'cdgeb-server-' + str(fe).zfill(2): mean([rtt for key,rtt in measurements.items() if \
                # front-end name == frontend_name
                key[1] == 'cdgeb-server-'+str(fe).zfill(2) and \
                # file name == filename
                key[2] == filename
                ]) for fe in range(1,17+1)}
            # print(means)
            best_fe_for_file[filename] = min(means, key=means.get)
            
        case 4:
            # Upon measurements of filename, where the probe is the closest one to the front-end, choose the front-end with the minimal RTT to the file.
            best_fe_for_file[filename] = min(measurements.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # probe_name == closest_probe_to_fe[frontend_name]
                    pair[0][0] == closest_probe_to_fe[pair[0][1]] and \
                    # and file == filename
                    pair[0][2] == filename \
                    else float('inf'))[0][1]
            
        case 5:
            # Just take the front-end with the minimal RTT to the file.
            best_fe_for_file[filename] = min(measurements.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # and file == filename
                    pair[0][2] == filename \
                    else float('inf'))[0][1] 
