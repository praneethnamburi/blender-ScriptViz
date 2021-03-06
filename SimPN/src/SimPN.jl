module SimPN
__precompile__(false)
using DifferentialEquations

function spring_mass(;k=10.0, m=1.0, tspan=(0.0, 5.0), x0=2.0, v0=0.0)
    function mdl!(du, u, p, t)
        x, v = u # position, velocity = dependent variables
        k, m = p # spring constant, mass = parameters
        du[1] = dx = v
        du[2] = dv = -(k/m)*x
    end
    prob = ODEProblem(mdl!, [x0, v0], tspan, [k, m])
    return solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8)
end

function int_fire_neuron_01(;tspan=(0.0, 1.0), τ=0.025)
    function mdl(u, p, t)
        τ, v∞ = p
        (1/τ)*(v∞ - u)
    end
    prob = ODEProblem(mdl, -70.0, tspan, [τ, -40.0])
    return solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8)
end

# reset the membrane potential when it crosses a threshold
function int_fire_neuron_02(;tspan=(0.0, 1.0), τ=0.025, v_rest=-70.0, v_th=-45.0, v∞ = -40.0)
    n_spike = 0
    function mdl(u, p, t)
        (1/τ)*(v∞ - u)
    end
    function cond(u, t, integrator)
        u - v_th # do something when u - v_th = 0
    end
    function affect!(integrator)
        n_spike += 1
        integrator.u = v_rest
    end
    cb = ContinuousCallback(cond, affect!)
    prob = ODEProblem(mdl, v_rest, tspan)
    sol = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8, callback=cb)
    println(n_spike)
    return sol
end

# add a second condition - reduce the time constant when neuron crosses reset
function int_fire_neuron_03(;tspan=(0.0, 1.0), τ=0.025, v_rest=-70.0, v_th=-45.0, v∞=-40.0, v_reset=-80.0)
    n_spike = 0
    spike_times = Float64[]
    function mdl(u, p, t)
        (1/τ)*(v∞ - u)
    end
    function cond(out, u, t, integrator)
        out[1] = u - v_th # membrane voltage u crossed threshold
        out[2] = u - v_rest #
    end
    function affect!(integrator, idx)
        if idx == 1 # neuron fired!
            n_spike += 1
            push!(spike_times, integrator.t)
            integrator.u = v_reset
        elseif idx == 2 # neuron crossed resting (from reset)
            τ = τ*1.3
        end
    end
    cb = VectorContinuousCallback(cond, affect!, 2)
    prob = ODEProblem(mdl, v_rest, tspan)
    sol = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8, callback=cb)
    println(n_spike)
    println(spike_times)
    return sol
end

# stepping using the integrator intrerface
function int_fire_neuron_04(;tspan=(0.0, 1.0), τ=0.025, v_rest=-70.0, v_th=-45.0, v∞ = -40.0)
    n_spike = 0
    function mdl(u, p, t)
        (1/τ)*(v∞ - u)
    end
    function cond(u, t, integrator)
        u - v_th # do something when u - v_th = 0
    end
    function affect!(integrator)
        n_spike += 1
        integrator.u = v_rest
    end
    cb = ContinuousCallback(cond, affect!, nothing)
    prob = ODEProblem(mdl, v_rest, tspan)
    integrator = init(prob, Tsit5(), reltol=1e-8, abstol=1e-8, callback=cb)
    return integrator # use step!(integrator) in the calling function to
end

# step through the integrator
function use_integrator(;dt=0.001)
    n1 = int_fire_neuron_04()
    t = Float64[]
    u = Float64[]
    push!(t, n1.t)
    push!(u, n1.u)
    while n1.t <= 1.0
        step!(n1, dt, true)
        push!(t, n1.t)
        push!(u, n1.u)
    end
    return t, u
end

function elastic_mass_01()
    g = 9.81 # m/s2 acceleration due to gravity
    m = 0.6 # kg mass of the ball (talus)
    k = 800 # kg/s2 spring constant (pantar fascia)
    β1 = 0.1 # m length from talus to calcaneus contacting the ground
    β = 0.03 # m length from talus to the pantar fascia insertion
    θo = π/3 # radians angle between plantar fascia and talus to back of foot line
    function mdl!(du, u, p, t)
        ys, yv = u # y position, y velocity
        du[1] = dys = yv # dys is the derivative of y position
        du[2] = dyv = (2.0/m)*tantheta(ys)*F_muscle(ys) - g
    end
    function tantheta(ys)
        if ys >= β1 || ys <= 0.0
            return 0.0
        else
            return ((ys/β1)/sqrt(1-(ys/β1)^2))
        end
    end
    function F_muscle(ys)
        if ys >= β1*sin(θo)
            return 0.0 # plantar fascia is slack
        else
            θ = asin(ys/β1)
            return 2*β*k*(cos(θ) - cos(θo)) # Hooke's law
        end
    end
    ys0 = β1*sin(θo)
    yv0 = 0
    tspan = (0.0, 0.5)
    prob = ODEProblem(mdl!, [ys0, yv0], tspan)
    sol = solve(prob, Tsit5(), reltol=1e-8, abstol=1e-8)
    ys_vec = ys_vec = [x[1] for x in sol.u]
    theta = atan.(tantheta.(ys_vec))*180.0/π
    fm = F_muscle.(ys_vec)
    return sol, theta, fm
end

Fmax = 3; b = 2; c = 2; d = 2;
passive_force(t) = Fmax/(1+exp(b-c*(t-d)));
plot(gc, 0:0.1:5.0)
end # module
