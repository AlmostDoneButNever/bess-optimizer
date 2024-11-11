from pyomo.environ import *

def optimize_revenue(initial_soc, data_input, prices, loads, final_soc_target, cap_settings, model_optimality_gap, model_time_limit):
  
    # Extract data
    data, basis, bess, service = data_input

    # Define power and energy capacities of BESS (if cap_settings is non-empty, the values in cap_settings will override the Excel settings)
    if cap_settings: 
        cap_power = cap_settings[0]
        cap_energy = cap_settings[1]
    else:
        cap_power = bess['cap_power']
        cap_energy = bess['cap_energy']

    # Define load profile (if available)
    if service['load'] == 1:
        load_profile = loads.value
        max_grid_purchase = 99999999  
        btm_ub = cap_power
    else:
        max_grid_purchase = 0
        btm_ub = 0


    # Define parameters
    schedule = data['schedule']
    beta = data['activation']
    gamma = data['reserve']
    dt = basis['dt']
    Seff = bess['s_eff']
    Ceff = bess['c_eff']
    Deff = bess['d_eff']
    desired_min_soc_limit = data['soc_limit']['min']
    desired_max_soc_limit = data['soc_limit']['max']
    max_soc_limit = bess['max_soc']
    min_soc_limit = bess['min_soc']
    daily_cycle_limit = bess['daily_cycle']

    price_df = prices
    p_arb = price_df['arb_energy_price']
    p_reg_up_c = price_df['reg_capacity_price']
    p_reg_up_e = price_df['reg_energy_price']
    p_reg_down_c = price_df['reg_down_capacity_price']
    p_reg_down_e = price_df['reg_down_energy_price']
    p_pres_c = price_df['pres_capacity_price']
    p_pres_e = price_df['pres_energy_price']
    p_cres_c = price_df['cres_capacity_price']
    p_cres_e = price_df['cres_energy_price']
    p_ec = price_df['ec_energy_price']
    p_dr_c = price_df['dr_capacity_price']
    p_dr_e = price_df['dr_energy_price']
    p_il_c = price_df['il_capacity_price']
    p_il_e = price_df['il_energy_price']

    total_time_period = len(price_df)
    T = range(1, total_time_period + 1)
    SOC_T = range(0, total_time_period + 1)

    # Define the model
    model = ConcreteModel()

    # Variables (lower and upper bounds defined in bounds ())
    model.SOC = Var(SOC_T, within=NonNegativeReals, bounds = (0, cap_energy))       # State of charge
    model.E_c = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))           # Actual energy charged into battery
    model.E_cr = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))          # Reserved energy content for charging
    model.E_ca = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))          # Activated energy content for charging
    model.E_d = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))           # Actual energy discharged from battery
    model.E_dr = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))          # Reserved energy content for discharging
    model.E_da = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))          # Activated energy content for discharging
    model.E_r = Var(T, within=NonNegativeReals, bounds = (0, cap_energy))           # Expected state of charge based on reserved energy content

    model.PC_arb = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Charging power allocated for arbitrage
    model.PD_arb = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Discharging power allocated for arbitrage
    model.P_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power))          # Power commitment for frequency regulation
    model.PC_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Power commitment for downward frequency regulation
    model.PD_reg = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Power commitment for upward frequency regulation
    model.P_pres = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Power commitment for primary reserve
    model.P_cres = Var(T, within=NonNegativeReals, bounds = (0, cap_power))         # Power commitment for contingency reserve

    model.P_ec = Var(T, within=NonNegativeReals, bounds = (0, max_grid_purchase))   # Power purchased from grid
    model.PL_ec = Var(T, within=NonNegativeReals, bounds = (0, max_grid_purchase))  # Power purchased from grid, used directly for loads
    model.PC_ec = Var(T, within=NonNegativeReals, bounds = (0, btm_ub))             # Power purchased from grid, charged into battery
    model.PD_L = Var(T, within=NonNegativeReals, bounds = (0, btm_ub))              # Power discharged from battery to fulfil loads
    model.P_dr = Var(T, within=NonNegativeReals, bounds = (0, btm_ub))              # Power commitment for demand response
    model.P_il = Var(T, within=NonNegativeReals, bounds = (0, btm_ub))              # Power commitment for interupttible load

    model.y_ch = Var(T, within=Binary)                                              # Binary variable to ensure charging and discharging do not occur concurrently 
    model.y_dr = Var(T, within=Binary)                                              # Binary variable to ensure demand response and interupttible load do not occur concurrently 

    model.R_arb = Var(T, within=Reals)                                              # Revenue due to arbitrage
    model.R_reg = Var(T, within=Reals)                                              # Revenue due to arbitrage
    model.R_pres = Var(T, within=Reals)                                             # Revenue due to primary reserve
    model.R_cres = Var(T, within=Reals)                                             # Revenue due to contingency reserve
    model.R_ec = Var(T, within=Reals)                                               # Revenue due to energy bills savings
    model.R_dr = Var(T, within=Reals)                                               # Revenue due to demand response
    model.R_il = Var(T, within=Reals)                                               # Revenue due to interupttible load


    # Objective function (EQ 1)
    model.obj = Objective(
        expr= sum(model.R_arb[t] + model.R_reg[t] + model.R_pres[t] + model.R_cres[t] 
                  + model.R_ec[t] + model.R_dr[t] + model.R_il[t] 
                  for t in T),        
        sense=maximize
    )

    # Revenue from arbitrage (EQ 2)
    def revenue_arbitrage_rule(model, t):
        return model.R_arb[t] == p_arb[t]  * (model.PD_arb[t] - model.PC_arb[t]) * dt
    model.revenue_arbitrage = Constraint(T, rule=revenue_arbitrage_rule)

    # Revenue from primary and contingency reserves (EQ 2), beta represents activation signal and is zero by default
    def revenue_primary_reserve_rule(model, t):
        return model.R_pres[t] == (p_pres_c[t]  * model.P_pres[t]
                                        + p_pres_e[t] * beta['pres'][t] * model.P_pres[t]) * dt
    model.revenue_preserve = Constraint(T, rule=revenue_primary_reserve_rule)

    def revenue_contingency_reserve_rule(model, t):
        return model.R_cres[t] == (p_cres_c[t]  * model.P_cres[t]
                                        + p_cres_e[t] * beta['cres'][t] * model.P_cres[t]) * dt
    model.revenue_creserve = Constraint(T, rule=revenue_contingency_reserve_rule)

    # Revenue from frequency regulation
    ## If the bid is symmetrical (same capacity for regulation up and down services)
    if service['reg_symmetric'] == 1:
        ### Revenue based on the committed capacity (regardless of up or down)(EQ 4)
        def revenue_regulation_rule(model, t):
            return model.R_reg[t] == (p_reg_up_c[t]  * model.P_reg[t]
                                            + p_reg_up_e[t] * beta['reg'][t] * model.P_reg[t]) * dt
        model.revenue_regulation = Constraint(T, rule=revenue_regulation_rule)

        ### Committed capacity is either used for regulation up or regulation down (both will not occur at the same time)(EQ 5)
        def reg_constraint_rule(model, t):
            return model.P_reg[t] == model.PC_reg[t]  + model.PD_reg[t] 
        model.reg_up_down = Constraint(T, rule=reg_constraint_rule)

    else:
        ### Revenue based on the upward and downward capacities, respectively (EQ 6) 
        def revenue_regulation_rule(model, t):
            return model.R_reg[t] == (p_reg_up_c[t]  * model.PD_reg[t] 
                                            + p_reg_down_c[t]  * model.PC_reg[t] 
                                            + p_reg_up_e[t] * beta['reg_up'][t] * model.PD_reg[t]
                                            - p_reg_down_e[t] * beta['reg_down'][t] * model.PC_reg[t]
                                            ) * dt
        model.revenue_regulation = Constraint(T, rule=revenue_regulation_rule)

    # Revenue from electricity bills savings (only if load is available) (EQ 7)
    def revenue_energy_charge_rule(model, t):
        if service['load'] == 1:
            return model.R_ec[t] == p_ec[t]  * (load_profile[t] - model.P_ec[t] * dt) 
        else:
            return model.R_ec[t] == 0
    model.revenue_energy_charge = Constraint(T, rule=revenue_energy_charge_rule)

    # Revenue from demand response (EQ 8)
    def revenue_demand_response_rule(model, t):
        return model.R_dr[t] == (p_dr_c[t]  * model.P_dr[t]
                                        + p_dr_e[t] * beta['dr'][t] * model.P_dr[t]) * dt
    model.revenue_demand_response = Constraint(T, rule=revenue_demand_response_rule)

    # Revenue from interruptible load (EQ 9)
    def revenue_interruptible_load_rule(model, t):
        return model.R_il[t] == (p_il_c[t]  * model.P_il[t]
                                        + p_il_e[t] * beta['il'][t] * model.P_il[t]) * dt
    model.revenue_interruptible_load = Constraint(T, rule=revenue_interruptible_load_rule)

    # Mutual exclusiveness of DR and IL (not occuring together)(EQ 10 and 11)
    def dr_binary_rule(model, t):
        return model.P_dr[t] <= cap_power * model.y_dr[t]
    model.dr_binary = Constraint(T, rule=dr_binary_rule)

    def il_binary_rule(model, t):
        return model.P_il[t] <= cap_power * (1 - model.y_dr[t])
    model.il_binary = Constraint(T, rule=il_binary_rule)

    # Allocation of grid electricity purchase to load or BESS (EQ 12)
    def total_grid_power_rule(model, t):
        return model.P_ec[t] == model.PL_ec[t] + model.PC_ec[t]
    model.total_grid_power = Constraint(T, rule=total_grid_power_rule)

    # Load fulfillment (EQ 13)
    if service['load'] == 1:
        def total_load_balance_rule(model, t):
            return (model.PL_ec[t] +  model.PD_L[t] + beta['dr'][t] * model.P_dr[t] + beta['il'][t] * model.P_il[t]) * dt == load_profile[t]
        model.total_load_balance = Constraint(T, rule=total_load_balance_rule)

    # Overall power balance when the battery is at charging state (EQ 14)
    def total_charge_rule(model, t):
        return model.PC_arb[t] + model.PC_reg[t] + model.PC_ec[t]  <= cap_power * model.y_ch[t]
    model.total_charge = Constraint(T, rule=total_charge_rule)

    # Overall power balance when the battery is at discharging state (EQ 15)
    def total_discharge_rule(model, t):
        return model.PD_arb[t] +  model.PD_reg[t] + model.P_pres[t] +  model.P_cres[t] \
                    + model.PD_L[t] + model.P_dr[t] +  model.P_il[t] <= cap_power * (1 - model.y_ch[t])
    model.total_discharge = Constraint(T, rule=total_discharge_rule)

    # Energy discharged from BESS for selling to the grid/curtailing loads  (EQ 16)
    def energy_discharge_rule(model, t):
        return model.E_d[t] == (model.PD_arb[t] 
                                + model.PD_L[t]
                                ) * dt
    model.energy_discharge = Constraint(T, rule=energy_discharge_rule)

    # Energy charged into BESS for arbitrage or satisfying local demand (EQ 17)
    def energy_charge_rule(model, t):
        return model.E_c[t] == (model.PC_arb[t]  
                                + model.PC_ec[t]  
                                ) * dt
    model.energy_charge = Constraint(T, rule=energy_charge_rule)

    # Energy reserved for ancillary services (discharge) (EQ 18)
    def energy_discharge_reserve_rule(model, t):
        return model.E_dr[t] == (
                                   gamma['reg'][t] * model.PD_reg[t]
                                +  gamma['pres'][t] * model.P_pres[t]
                                +  gamma['cres'][t] * model.P_cres[t]
                                +  gamma['dr'][t] * model.P_dr[t]
                                +  gamma['il'][t] * model.P_il[t]
                                ) * dt
    model.energy_discharge_reserve = Constraint(T, rule=energy_discharge_reserve_rule)

    # Energy reserved for ancillary services (charge) (EQ 19)
    def energy_charge_reserve_rule(model, t):
        return model.E_cr[t] == (gamma['reg'][t] * model.PC_reg[t]) * dt
    model.energy_charge_reserve = Constraint(T, rule=energy_charge_reserve_rule)

    # Expected state of charge based on reserved energy (EQ 20)
    def energy_reserve_rule(model, t):
        return model.E_r[t] == model.SOC[t-1]* Seff + (model.E_c[t] + model.E_cr[t]) * Ceff - (model.E_d[t] + model.E_dr[t]) / Deff 
    model.energy_reserve = Constraint(T, rule=energy_reserve_rule)

    # Upper and lower limits of BESS (EQ 21)
    def soc_lower_limit_constraint(model, t):
        return model.E_r[t] >= cap_energy * desired_min_soc_limit[t]
    model.SOC_lower_limit = Constraint(T, rule=soc_lower_limit_constraint)

    def soc_upper_limit_constraint(model, t):
        return model.E_r[t] <= cap_energy * desired_max_soc_limit[t]
    model.SOC_upper_limit = Constraint(T, rule=soc_upper_limit_constraint)

    # Activated energy discharged from BESS (EQ 22)
    def energy_discharge_activated_rule(model, t):
        return model.E_da[t] == (
                                  beta['reg_up'][t] * model.PD_reg[t]
                                + beta['pres'][t] * model.P_pres[t]
                                + beta['cres'][t] * model.P_cres[t]
                                + beta['dr'][t] * model.P_dr[t]
                                + beta['il'][t] * model.P_il[t]
                                ) * dt
    model.energy_discharge_activated = Constraint(T, rule=energy_discharge_activated_rule)

    # Activated energy charged into BESS (EQ 23)
    def energy_charge_activated_rule(model, t):
        return model.E_ca[t] == (  
                                beta['reg_down'][t] * model.PC_reg[t]
                                ) * dt
    model.energy_charge_activated = Constraint(T, rule=energy_charge_activated_rule)

    # State of charge of BESS (EQ 24)
    def soc_constraints(model, t):
        if t == 0:
            return model.SOC[t] == initial_soc
        else:
            return model.SOC[t] == model.SOC[t-1] * Seff + (model.E_c[t] + model.E_ca[t]) * Ceff - (model.E_d[t] + model.E_da[t])/Deff
    model.SOC_constraints = Constraint(SOC_T, rule=soc_constraints)

    # Cycle limits
    ## Without activation signal (EQs 27 and 28)
    if service['reg_activate'] != 1:

        def cycle_charge_constraint(model):
            return sum(model.PC_arb[t] + model.PC_ec[t] +  model.PC_reg[t] * gamma['reg'][t] for t in T)*dt <= daily_cycle_limit * cap_energy * (max_soc_limit - min_soc_limit)
        model.cycle_charge = Constraint(rule=cycle_charge_constraint)

        def cycle_discharge_constraint(model):
            return sum(model.PD_arb[t] + model.PD_L[t] + model.PD_reg[t] * gamma['reg'][t] for t in T)*dt <= daily_cycle_limit * cap_energy * (max_soc_limit - min_soc_limit)
        model.cycle_discharge = Constraint(rule=cycle_discharge_constraint)

    else:
    # With activation signal (EQs 25 and 26)   
        def cycle_charge_constraint(model):
            return sum(model.PC_arb[t] + model.PC_ec[t] +  model.PC_reg[t] * beta['reg_down'][t] for t in T)*dt <= daily_cycle_limit * cap_energy * (max_soc_limit - min_soc_limit)
        model.cycle_charge = Constraint(rule=cycle_charge_constraint)

        def cycle_discharge_constraint(model):
            return sum(model.PD_arb[t] + model.PD_L[t] + model.PD_reg[t] * beta['reg_up'][t] for t in T)*dt <= daily_cycle_limit * cap_energy * (max_soc_limit - min_soc_limit)
        model.cycle_discharge = Constraint(rule=cycle_discharge_constraint)


    # Service availability (EQ 29) - (the value 999999 is used to extend the upper limit of variables, so that the variables will be zero if service/schedule is zero, but any positive numbers if non-zero) 

    def arbitrage_availability_rule(model, t):
        return model.PC_arb[t] + model.PD_arb[t] <= service['arb'] * schedule['arb'].loc[t] * 999999
    model.arbitrage_availability = Constraint(T, rule=arbitrage_availability_rule)

    def regulation_up_availability_rule(model, t):
        if service['reg_activate'] != 1:
            return model.PD_reg[t] <= service['reg'] * schedule['reg'].loc[t] * 999999
        else: 
            return model.PD_reg[t] <= beta['reg_up'][t] * service['reg'] * schedule['reg'].loc[t] * 999999
    model.regulation_up_availability = Constraint(T, rule=regulation_up_availability_rule)

    def regulation_down_availability_rule(model, t):
        if service['reg_activate'] != 1:
            return model.PC_reg[t]  <= service['reg'] * schedule['reg'].loc[t] * 999999
        else:
            return model.PC_reg[t]  <= beta['reg_down'][t] * service['reg'] * schedule['reg'].loc[t] * 999999

    model.regulation_down_availability = Constraint(T, rule=regulation_down_availability_rule)

    def preserve_availability_rule(model, t):
        return model.P_pres[t] <= service['pres'] * schedule['pres'].loc[t] * 999999
    model.preserve_availability = Constraint(T, rule=preserve_availability_rule)

    def creserve_availability_rule(model, t):
        return model.P_cres[t] <= service['cres'] * schedule['cres'].loc[t] * 999999
    model.creserve_availability = Constraint(T, rule=creserve_availability_rule)

    def energy_charge_availability_rule(model, t):
        return model.P_ec[t] <= service['ec'] * schedule['ec'].loc[t] * 999999
    model.energy_charge_availability = Constraint(T, rule=energy_charge_availability_rule)

    def demand_response_availability_rule(model, t):
        return model.P_dr[t] <= service['dr'] * schedule['dr'].loc[t] * 999999
    model.demand_response_availability = Constraint(T, rule=demand_response_availability_rule)

    def interruptible_load_availability_rule(model, t):
        return model.P_il[t] <= service['il'] * schedule['il'].loc[t] * 999999
    model.interruptible_load_availability = Constraint(T, rule=interruptible_load_availability_rule)

    #### Additional constraint if state of charge needs to reach certain level by the end of a day, not used by default
    if final_soc_target:
        def soc_final_state_constraint(model):
            end_t = SOC_T[-1]
            return model.SOC[end_t] == bess['initial_soc'] * cap_energy
        model.SOC_final = Constraint(rule=soc_final_state_constraint)


    # Solve the model
    # solver = SolverFactory('glpk', executable = 'glpk\w64\glpsol.exe')
    solver = SolverFactory('glpk')
    solver.options['mipgap'] = model_optimality_gap  
    solver.options['tmlim'] = model_time_limit
    results = solver.solve(model, tee=False)

    # Extract results 
    schedule_dict = {}
    revenue_dict = {}

    schedule_dict['arb_charge'] = [model.PC_arb[t].value for t in T]  
    schedule_dict['arb_discharge'] = [model.PD_arb[t].value for t in T]
    schedule_dict['reg_down'] = [model.PC_reg[t].value for t in T] 
    schedule_dict['reg_up'] = [model.PD_reg[t].value for t in T]  
    schedule_dict['pres'] = [model.P_pres[t].value for t in T]  
    schedule_dict['cres'] = [model.P_cres[t].value for t in T]  
    schedule_dict['dr'] = [model.P_dr[t].value for t in T] 
    schedule_dict['il'] = [model.P_il[t].value for t in T] 
    schedule_dict['grid_purchase'] = [model.P_ec[t].value for t in T]  
    schedule_dict['grid_to_storage'] = [model.PC_ec[t].value for t in T]  
    schedule_dict['grid_to_load'] = [model.PL_ec[t].value for t in T] 
    schedule_dict['storage_to_load'] = [model.PD_L[t].value for t in T]  
    schedule_dict['soc'] = [model.SOC[t].value for t in SOC_T]  

    revenue_dict['arb'] =  [model.R_arb[t]() for t in T] 
    revenue_dict['reg'] = [model.R_reg[t]() for t in T ]
    revenue_dict['pres'] = [model.R_pres[t]() for t in T ]
    revenue_dict['cres'] = [model.R_cres[t]() for t in T] 
    revenue_dict['dr'] = [model.R_dr[t]() for t in T ]
    revenue_dict['il'] = [model.R_il[t]() for t in T ]
    revenue_dict['ec'] = [model.R_ec[t]() for t in T]

    # Return the results
    return model, model.obj(), schedule_dict, revenue_dict