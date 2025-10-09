--
-- PostgreSQL database dump
--

\restrict hlvI0xcMHq0TDhrAufENY3TLbfaZ2CgpHOMhsiwoHTzAy4sSlKitDYI7ufwvIRN

-- Dumped from database version 15.14
-- Dumped by pg_dump version 15.14

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: projectitemstatus; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.projectitemstatus AS ENUM (
    'PENDING',
    'SUGGESTED',
    'DECIDED',
    'PROCURED',
    'FULFILLED',
    'PAID',
    'CASH_RECEIVED'
);


ALTER TYPE public.projectitemstatus OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: budget_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.budget_data (
    id integer NOT NULL,
    budget_date date NOT NULL,
    available_budget numeric(15,2) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.budget_data OWNER TO postgres;

--
-- Name: budget_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.budget_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.budget_data_id_seq OWNER TO postgres;

--
-- Name: budget_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.budget_data_id_seq OWNED BY public.budget_data.id;


--
-- Name: cashflow_events; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cashflow_events (
    id integer NOT NULL,
    related_decision_id integer,
    event_type character varying(10) NOT NULL,
    forecast_type character varying(10) NOT NULL,
    event_date date NOT NULL,
    amount numeric(15,2) NOT NULL,
    description text,
    is_cancelled boolean NOT NULL,
    cancelled_at timestamp with time zone,
    cancelled_by_id integer,
    cancellation_reason text,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.cashflow_events OWNER TO postgres;

--
-- Name: cashflow_events_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.cashflow_events_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.cashflow_events_id_seq OWNER TO postgres;

--
-- Name: cashflow_events_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.cashflow_events_id_seq OWNED BY public.cashflow_events.id;


--
-- Name: decision_factor_weights; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.decision_factor_weights (
    id integer NOT NULL,
    factor_name character varying(100) NOT NULL,
    weight integer NOT NULL,
    description text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    CONSTRAINT check_weight_range CHECK (((weight >= 1) AND (weight <= 10)))
);


ALTER TABLE public.decision_factor_weights OWNER TO postgres;

--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.decision_factor_weights_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.decision_factor_weights_id_seq OWNER TO postgres;

--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.decision_factor_weights_id_seq OWNED BY public.decision_factor_weights.id;


--
-- Name: delivery_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.delivery_options (
    id integer NOT NULL,
    project_item_id integer NOT NULL,
    delivery_slot integer,
    delivery_date date NOT NULL,
    invoice_timing_type character varying(20) NOT NULL,
    invoice_issue_date date,
    invoice_days_after_delivery integer,
    invoice_amount_per_unit numeric(12,2) NOT NULL,
    preference_rank integer,
    notes text,
    is_active boolean,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.delivery_options OWNER TO postgres;

--
-- Name: delivery_options_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.delivery_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.delivery_options_id_seq OWNER TO postgres;

--
-- Name: delivery_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.delivery_options_id_seq OWNED BY public.delivery_options.id;


--
-- Name: finalized_decisions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.finalized_decisions (
    id integer NOT NULL,
    run_id uuid,
    project_id integer NOT NULL,
    project_item_id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    procurement_option_id integer NOT NULL,
    purchase_date date NOT NULL,
    delivery_date date NOT NULL,
    quantity integer NOT NULL,
    final_cost numeric(12,2) NOT NULL,
    status character varying(20) NOT NULL,
    delivery_option_id integer,
    forecast_invoice_timing_type character varying(20) NOT NULL,
    forecast_invoice_issue_date date,
    forecast_invoice_days_after_delivery integer,
    forecast_invoice_amount numeric(12,2),
    actual_invoice_issue_date date,
    actual_invoice_amount numeric(12,2),
    actual_invoice_received_date date,
    invoice_entered_by_id integer,
    invoice_entered_at timestamp with time zone,
    decision_maker_id integer NOT NULL,
    decision_date timestamp with time zone NOT NULL,
    finalized_at timestamp with time zone,
    finalized_by_id integer,
    is_manual_edit boolean,
    notes text,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    bunch_id character varying(50),
    bunch_name character varying(200)
);


ALTER TABLE public.finalized_decisions OWNER TO postgres;

--
-- Name: COLUMN finalized_decisions.bunch_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.finalized_decisions.bunch_id IS 'Bunch identifier for phased finalization (e.g., BUNCH_1, BUNCH_2)';


--
-- Name: COLUMN finalized_decisions.bunch_name; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.finalized_decisions.bunch_name IS 'Human-readable bunch name (e.g., High Priority - Month 1)';


--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.finalized_decisions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.finalized_decisions_id_seq OWNER TO postgres;

--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.finalized_decisions_id_seq OWNED BY public.finalized_decisions.id;


--
-- Name: optimization_results; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.optimization_results (
    id integer NOT NULL,
    run_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now(),
    project_id integer,
    item_code character varying(50) NOT NULL,
    procurement_option_id integer NOT NULL,
    purchase_time integer NOT NULL,
    delivery_time integer NOT NULL,
    quantity integer NOT NULL,
    final_cost numeric(12,2) NOT NULL
);


ALTER TABLE public.optimization_results OWNER TO postgres;

--
-- Name: optimization_results_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.optimization_results_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.optimization_results_id_seq OWNER TO postgres;

--
-- Name: optimization_results_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.optimization_results_id_seq OWNED BY public.optimization_results.id;


--
-- Name: optimization_runs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.optimization_runs (
    run_id uuid NOT NULL,
    run_timestamp timestamp with time zone DEFAULT now(),
    request_parameters json NOT NULL,
    status character varying(20) NOT NULL
);


ALTER TABLE public.optimization_runs OWNER TO postgres;

--
-- Name: procurement_options; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.procurement_options (
    id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    supplier_name text NOT NULL,
    base_cost numeric(12,2) NOT NULL,
    lomc_lead_time integer,
    discount_bundle_threshold integer,
    discount_bundle_percent numeric(5,2),
    payment_terms json NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone,
    is_active boolean
);


ALTER TABLE public.procurement_options OWNER TO postgres;

--
-- Name: procurement_options_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.procurement_options_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.procurement_options_id_seq OWNER TO postgres;

--
-- Name: procurement_options_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.procurement_options_id_seq OWNED BY public.procurement_options.id;


--
-- Name: project_assignments; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_assignments (
    user_id integer NOT NULL,
    project_id integer NOT NULL,
    assigned_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.project_assignments OWNER TO postgres;

--
-- Name: project_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_items (
    id integer NOT NULL,
    project_id integer NOT NULL,
    item_code character varying(50) NOT NULL,
    item_name text,
    quantity integer NOT NULL,
    delivery_options json NOT NULL,
    status public.projectitemstatus NOT NULL,
    external_purchase boolean,
    decision_date date,
    procurement_date date,
    payment_date date,
    invoice_submission_date date,
    expected_cash_in_date date,
    actual_cash_in_date date,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.project_items OWNER TO postgres;

--
-- Name: project_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.project_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_items_id_seq OWNER TO postgres;

--
-- Name: project_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.project_items_id_seq OWNED BY public.project_items.id;


--
-- Name: project_phases; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project_phases (
    id integer NOT NULL,
    project_id integer NOT NULL,
    phase_name character varying(100) NOT NULL,
    start_date date NOT NULL,
    end_date date NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone
);


ALTER TABLE public.project_phases OWNER TO postgres;

--
-- Name: project_phases_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.project_phases_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_phases_id_seq OWNER TO postgres;

--
-- Name: project_phases_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.project_phases_id_seq OWNED BY public.project_phases.id;


--
-- Name: projects; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.projects (
    id integer NOT NULL,
    project_code character varying(50) NOT NULL,
    name text NOT NULL,
    priority_weight integer NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean,
    CONSTRAINT check_priority_weight_range CHECK (((priority_weight >= 1) AND (priority_weight <= 10)))
);


ALTER TABLE public.projects OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.projects_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.projects_id_seq OWNER TO postgres;

--
-- Name: projects_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.projects_id_seq OWNED BY public.projects.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    is_active boolean
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: budget_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_data ALTER COLUMN id SET DEFAULT nextval('public.budget_data_id_seq'::regclass);


--
-- Name: cashflow_events id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events ALTER COLUMN id SET DEFAULT nextval('public.cashflow_events_id_seq'::regclass);


--
-- Name: decision_factor_weights id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights ALTER COLUMN id SET DEFAULT nextval('public.decision_factor_weights_id_seq'::regclass);


--
-- Name: delivery_options id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options ALTER COLUMN id SET DEFAULT nextval('public.delivery_options_id_seq'::regclass);


--
-- Name: finalized_decisions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions ALTER COLUMN id SET DEFAULT nextval('public.finalized_decisions_id_seq'::regclass);


--
-- Name: optimization_results id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results ALTER COLUMN id SET DEFAULT nextval('public.optimization_results_id_seq'::regclass);


--
-- Name: procurement_options id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_options ALTER COLUMN id SET DEFAULT nextval('public.procurement_options_id_seq'::regclass);


--
-- Name: project_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items ALTER COLUMN id SET DEFAULT nextval('public.project_items_id_seq'::regclass);


--
-- Name: project_phases id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases ALTER COLUMN id SET DEFAULT nextval('public.project_phases_id_seq'::regclass);


--
-- Name: projects id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects ALTER COLUMN id SET DEFAULT nextval('public.projects_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Data for Name: budget_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.budget_data (id, budget_date, available_budget, created_at, updated_at) FROM stdin;
374	2025-01-01	50000.00	2025-10-09 14:37:30.987952+00	\N
375	2025-01-31	75000.00	2025-10-09 14:37:30.987952+00	\N
376	2025-03-02	100000.00	2025-10-09 14:37:30.987952+00	\N
377	2025-04-01	125000.00	2025-10-09 14:37:30.987952+00	\N
378	2025-05-01	150000.00	2025-10-09 14:37:30.987952+00	\N
379	2025-05-31	175000.00	2025-10-09 14:37:30.987952+00	\N
380	2025-06-30	200000.00	2025-10-09 14:37:30.987952+00	\N
381	2025-07-30	225000.00	2025-10-09 14:37:30.987952+00	\N
382	2025-08-29	250000.00	2025-10-09 14:37:30.987952+00	\N
383	2025-09-28	275000.00	2025-10-09 14:37:30.987952+00	\N
384	2025-10-28	300000.00	2025-10-09 14:37:30.987952+00	\N
385	2025-11-27	325000.00	2025-10-09 14:37:30.987952+00	\N
\.


--
-- Data for Name: cashflow_events; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cashflow_events (id, related_decision_id, event_type, forecast_type, event_date, amount, description, is_cancelled, cancelled_at, cancelled_by_id, cancellation_reason, created_at) FROM stdin;
\.


--
-- Data for Name: decision_factor_weights; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.decision_factor_weights (id, factor_name, weight, description, created_at, updated_at) FROM stdin;
249	cost_minimization	9	Prioritize minimizing total procurement cost	2025-10-09 14:37:30.994309+00	\N
250	lead_time_optimization	8	Optimize delivery times to meet project deadlines	2025-10-09 14:37:30.994309+00	\N
251	supplier_rating	7	Consider supplier reliability and quality ratings	2025-10-09 14:37:30.994309+00	\N
252	cash_flow_balance	8	Balance cash outflows across time periods	2025-10-09 14:37:30.994309+00	\N
253	bundle_discount_maximization	6	Maximize bulk purchase discounts when possible	2025-10-09 14:37:30.994309+00	\N
254	quality_assurance	7	Ensure high-quality materials and workmanship	2025-10-09 14:37:30.994309+00	\N
255	risk_mitigation	6	Minimize procurement and delivery risks	2025-10-09 14:37:30.994309+00	\N
256	sustainability	5	Prefer environmentally friendly options	2025-10-09 14:37:30.994309+00	\N
\.


--
-- Data for Name: delivery_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.delivery_options (id, project_item_id, delivery_slot, delivery_date, invoice_timing_type, invoice_issue_date, invoice_days_after_delivery, invoice_amount_per_unit, preference_rank, notes, is_active, created_at, updated_at) FROM stdin;
3101	1599	1	2025-04-19	RELATIVE	2025-05-24	35	130.64	1	Delivery option 1 for Electrical Cables - 3-Core 2.5mm²	t	2025-10-09 14:37:30.967573+00	\N
3102	1599	2	2025-05-05	RELATIVE	2025-07-17	73	115.38	2	Delivery option 2 for Electrical Cables - 3-Core 2.5mm²	t	2025-10-09 14:37:30.967573+00	\N
3103	1600	1	2025-04-23	RELATIVE	2025-07-12	80	130.91	1	Delivery option 1 for Cement - Portland Type I	t	2025-10-09 14:37:30.967573+00	\N
3104	1600	2	2025-05-11	RELATIVE	2025-06-17	37	110.59	2	Delivery option 2 for Cement - Portland Type I	t	2025-10-09 14:37:30.967573+00	\N
3105	1551	1	2025-03-31	RELATIVE	2025-06-08	69	128.59	1	Delivery option 1 for Ready-Mix Concrete - Grade C25	t	2025-10-09 14:37:30.967573+00	\N
3106	1551	2	2025-04-21	RELATIVE	2025-06-10	50	162.97	2	Delivery option 2 for Ready-Mix Concrete - Grade C25	t	2025-10-09 14:37:30.967573+00	\N
3107	1552	1	2025-04-28	RELATIVE	2025-05-29	31	123.09	1	Delivery option 1 for Concrete Mixer - 3m³	t	2025-10-09 14:37:30.967573+00	\N
3108	1552	2	2025-05-07	RELATIVE	2025-08-04	89	171.57	2	Delivery option 2 for Concrete Mixer - 3m³	t	2025-10-09 14:37:30.967573+00	\N
3109	1553	1	2025-03-03	RELATIVE	2025-05-18	76	104.58	1	Delivery option 1 for Power Tools - Construction Set	t	2025-10-09 14:37:30.967573+00	\N
3110	1553	2	2025-03-17	RELATIVE	2025-05-24	68	109.99	2	Delivery option 2 for Power Tools - Construction Set	t	2025-10-09 14:37:30.967573+00	\N
3111	1554	1	2025-04-04	RELATIVE	2025-06-08	65	170.95	1	Delivery option 1 for Perimeter Fencing - Chain Link	t	2025-10-09 14:37:30.967573+00	\N
3112	1554	2	2025-04-24	RELATIVE	2025-06-13	50	97.24	2	Delivery option 2 for Perimeter Fencing - Chain Link	t	2025-10-09 14:37:30.967573+00	\N
3113	1555	1	2025-05-07	RELATIVE	2025-06-21	45	145.25	1	Delivery option 1 for Water Pipes - PVC 100mm	t	2025-10-09 14:37:30.967573+00	\N
3114	1555	2	2025-05-17	RELATIVE	2025-08-09	84	95.89	2	Delivery option 2 for Water Pipes - PVC 100mm	t	2025-10-09 14:37:30.967573+00	\N
3115	1556	1	2025-03-27	RELATIVE	2025-06-25	90	108.17	1	Delivery option 1 for Irrigation System - Drip Type	t	2025-10-09 14:37:30.967573+00	\N
3116	1556	2	2025-04-07	RELATIVE	2025-06-09	63	176.16	2	Delivery option 2 for Irrigation System - Drip Type	t	2025-10-09 14:37:30.967573+00	\N
3117	1557	1	2025-05-22	RELATIVE	2025-08-04	74	95.97	1	Delivery option 1 for Coarse Aggregate - 20mm	t	2025-10-09 14:37:30.967573+00	\N
3118	1557	2	2025-06-10	RELATIVE	2025-07-28	48	140.57	2	Delivery option 2 for Coarse Aggregate - 20mm	t	2025-10-09 14:37:30.967573+00	\N
3119	1558	1	2025-03-03	RELATIVE	2025-05-01	59	143.45	1	Delivery option 1 for Landscaping - Trees & Shrubs	t	2025-10-09 14:37:30.967573+00	\N
3120	1558	2	2025-03-14	RELATIVE	2025-04-27	44	144.20	2	Delivery option 2 for Landscaping - Trees & Shrubs	t	2025-10-09 14:37:30.967573+00	\N
3121	1559	1	2025-03-14	RELATIVE	2025-04-18	35	133.82	1	Delivery option 1 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3122	1559	2	2025-04-03	RELATIVE	2025-06-17	75	158.43	2	Delivery option 2 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3123	1560	1	2025-04-11	RELATIVE	2025-05-20	39	116.69	1	Delivery option 1 for Fire Extinguishers - 10kg	t	2025-10-09 14:37:30.967573+00	\N
3124	1560	2	2025-05-02	RELATIVE	2025-07-29	88	93.96	2	Delivery option 2 for Fire Extinguishers - 10kg	t	2025-10-09 14:37:30.967573+00	\N
3125	1561	1	2025-05-14	RELATIVE	2025-07-16	63	144.94	1	Delivery option 1 for Ready-Mix Concrete - Grade C30	t	2025-10-09 14:37:30.967573+00	\N
3126	1561	2	2025-05-25	RELATIVE	2025-08-16	83	150.14	2	Delivery option 2 for Ready-Mix Concrete - Grade C30	t	2025-10-09 14:37:30.967573+00	\N
3127	1562	1	2025-03-22	RELATIVE	2025-05-15	54	96.66	1	Delivery option 1 for Aluminum Windows - Double Glazed	t	2025-10-09 14:37:30.967573+00	\N
3128	1562	2	2025-04-06	RELATIVE	2025-06-24	79	91.87	2	Delivery option 2 for Aluminum Windows - Double Glazed	t	2025-10-09 14:37:30.967573+00	\N
3129	1563	1	2025-04-22	RELATIVE	2025-05-23	31	114.89	1	Delivery option 1 for LED Light Fixtures - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3130	1563	2	2025-05-13	RELATIVE	2025-08-05	84	109.43	2	Delivery option 2 for LED Light Fixtures - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3131	1564	1	2025-03-27	RELATIVE	2025-05-30	64	150.15	1	Delivery option 1 for Roofing Membrane - EPDM	t	2025-10-09 14:37:30.967573+00	\N
3132	1564	2	2025-04-17	RELATIVE	2025-06-25	69	145.30	2	Delivery option 2 for Roofing Membrane - EPDM	t	2025-10-09 14:37:30.967573+00	\N
3133	1565	1	2025-05-30	RELATIVE	2025-08-25	87	143.93	1	Delivery option 1 for Ventilation Fans - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3134	1565	2	2025-06-18	RELATIVE	2025-08-25	68	114.49	2	Delivery option 2 for Ventilation Fans - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3135	1566	1	2025-04-16	RELATIVE	2025-06-05	50	146.89	1	Delivery option 1 for Formwork - Steel Panels	t	2025-10-09 14:37:30.967573+00	\N
3136	1566	2	2025-05-03	RELATIVE	2025-06-18	46	126.92	2	Delivery option 2 for Formwork - Steel Panels	t	2025-10-09 14:37:30.967573+00	\N
3137	1567	1	2025-05-20	RELATIVE	2025-08-11	83	162.11	1	Delivery option 1 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3138	1567	2	2025-06-08	RELATIVE	2025-09-05	89	152.62	2	Delivery option 2 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3139	1568	1	2025-03-22	RELATIVE	2025-05-05	44	127.60	1	Delivery option 1 for Meeting Room Furniture Set	t	2025-10-09 14:37:30.967573+00	\N
3140	1568	2	2025-04-01	RELATIVE	2025-05-14	43	104.41	2	Delivery option 2 for Meeting Room Furniture Set	t	2025-10-09 14:37:30.967573+00	\N
3141	1569	1	2025-03-07	RELATIVE	2025-04-29	53	155.91	1	Delivery option 1 for Thermal Insulation - Rockwool	t	2025-10-09 14:37:30.967573+00	\N
3142	1569	2	2025-03-17	RELATIVE	2025-05-31	75	97.78	2	Delivery option 2 for Thermal Insulation - Rockwool	t	2025-10-09 14:37:30.967573+00	\N
3143	1570	1	2025-04-08	RELATIVE	2025-05-10	32	91.63	1	Delivery option 1 for Excavator - 20 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3144	1570	2	2025-04-22	RELATIVE	2025-05-26	34	109.32	2	Delivery option 2 for Excavator - 20 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3145	1571	1	2025-04-30	RELATIVE	2025-07-26	87	162.83	1	Delivery option 1 for Cleaning Equipment - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3146	1571	2	2025-05-13	RELATIVE	2025-06-15	33	171.03	2	Delivery option 2 for Cleaning Equipment - Industrial	t	2025-10-09 14:37:30.967573+00	\N
3147	1572	1	2025-05-28	RELATIVE	2025-08-13	77	107.58	1	Delivery option 1 for Personal Protective Equipment Set	t	2025-10-09 14:37:30.967573+00	\N
3148	1572	2	2025-06-08	RELATIVE	2025-08-22	75	127.44	2	Delivery option 2 for Personal Protective Equipment Set	t	2025-10-09 14:37:30.967573+00	\N
3149	1573	1	2025-03-04	RELATIVE	2025-05-10	67	170.23	1	Delivery option 1 for Steel Doors - Fire Rated	t	2025-10-09 14:37:30.967573+00	\N
3150	1573	2	2025-03-23	RELATIVE	2025-05-16	54	99.97	2	Delivery option 2 for Steel Doors - Fire Rated	t	2025-10-09 14:37:30.967573+00	\N
3151	1574	1	2025-03-21	RELATIVE	2025-05-18	58	166.96	1	Delivery option 1 for Maintenance Tools - Complete Set	t	2025-10-09 14:37:30.967573+00	\N
3152	1574	2	2025-04-01	RELATIVE	2025-06-04	64	127.85	2	Delivery option 2 for Maintenance Tools - Complete Set	t	2025-10-09 14:37:30.967573+00	\N
3153	1575	1	2025-04-01	RELATIVE	2025-06-08	68	107.47	1	Delivery option 1 for Landscaping - Trees & Shrubs	t	2025-10-09 14:37:30.967573+00	\N
3154	1575	2	2025-04-22	RELATIVE	2025-06-30	69	98.04	2	Delivery option 2 for Landscaping - Trees & Shrubs	t	2025-10-09 14:37:30.967573+00	\N
3155	1576	1	2025-04-05	RELATIVE	2025-05-11	36	114.63	1	Delivery option 1 for Reinforcement Bars - Grade 60	t	2025-10-09 14:37:30.967573+00	\N
3156	1576	2	2025-04-26	RELATIVE	2025-07-14	79	101.15	2	Delivery option 2 for Reinforcement Bars - Grade 60	t	2025-10-09 14:37:30.967573+00	\N
3157	1577	1	2025-05-14	RELATIVE	2025-07-16	63	143.18	1	Delivery option 1 for Access Control System	t	2025-10-09 14:37:30.967573+00	\N
3158	1577	2	2025-06-01	RELATIVE	2025-08-30	90	133.45	2	Delivery option 2 for Access Control System	t	2025-10-09 14:37:30.967573+00	\N
3159	1578	1	2025-03-20	RELATIVE	2025-05-20	61	140.94	1	Delivery option 1 for Thermal Insulation - Rockwool	t	2025-10-09 14:37:30.967573+00	\N
3160	1578	2	2025-04-03	RELATIVE	2025-05-16	43	153.57	2	Delivery option 2 for Thermal Insulation - Rockwool	t	2025-10-09 14:37:30.967573+00	\N
3161	1579	1	2025-05-16	RELATIVE	2025-07-01	46	97.11	1	Delivery option 1 for Ready-Mix Concrete - Grade C25	t	2025-10-09 14:37:30.967573+00	\N
3162	1579	2	2025-06-05	RELATIVE	2025-09-03	90	125.46	2	Delivery option 2 for Ready-Mix Concrete - Grade C25	t	2025-10-09 14:37:30.967573+00	\N
3163	1580	1	2025-03-07	RELATIVE	2025-05-24	78	158.95	1	Delivery option 1 for Sewage Pipes - HDPE 200mm	t	2025-10-09 14:37:30.967573+00	\N
3164	1580	2	2025-03-19	RELATIVE	2025-06-07	80	163.81	2	Delivery option 2 for Sewage Pipes - HDPE 200mm	t	2025-10-09 14:37:30.967573+00	\N
3165	1581	1	2025-03-15	RELATIVE	2025-06-06	83	143.83	1	Delivery option 1 for Access Control System	t	2025-10-09 14:37:30.967573+00	\N
3166	1581	2	2025-03-23	RELATIVE	2025-06-19	88	108.22	2	Delivery option 2 for Access Control System	t	2025-10-09 14:37:30.967573+00	\N
3167	1582	1	2025-05-03	RELATIVE	2025-07-07	65	104.92	1	Delivery option 1 for Interior Paint - Low VOC	t	2025-10-09 14:37:30.967573+00	\N
3168	1582	2	2025-05-23	RELATIVE	2025-07-24	62	128.31	2	Delivery option 2 for Interior Paint - Low VOC	t	2025-10-09 14:37:30.967573+00	\N
3169	1583	1	2025-05-12	RELATIVE	2025-07-24	73	133.56	1	Delivery option 1 for Marble Tiles - 30x30cm	t	2025-10-09 14:37:30.967573+00	\N
3170	1583	2	2025-05-30	RELATIVE	2025-07-29	60	125.85	2	Delivery option 2 for Marble Tiles - 30x30cm	t	2025-10-09 14:37:30.967573+00	\N
3171	1584	1	2025-05-07	RELATIVE	2025-07-27	81	126.72	1	Delivery option 1 for Maintenance Tools - Complete Set	t	2025-10-09 14:37:30.967573+00	\N
3172	1584	2	2025-05-21	RELATIVE	2025-07-23	63	118.91	2	Delivery option 2 for Maintenance Tools - Complete Set	t	2025-10-09 14:37:30.967573+00	\N
3173	1585	1	2025-03-21	RELATIVE	2025-06-09	80	146.27	1	Delivery option 1 for Communication Equipment - Radio	t	2025-10-09 14:37:30.967573+00	\N
3174	1585	2	2025-04-04	RELATIVE	2025-06-25	82	171.48	2	Delivery option 2 for Communication Equipment - Radio	t	2025-10-09 14:37:30.967573+00	\N
3175	1586	1	2025-05-13	RELATIVE	2025-06-24	42	149.73	1	Delivery option 1 for Excavator - 20 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3176	1586	2	2025-06-01	RELATIVE	2025-07-08	37	143.96	2	Delivery option 2 for Excavator - 20 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3177	1587	1	2025-04-20	RELATIVE	2025-07-11	82	162.04	1	Delivery option 1 for Computer Equipment - Desktop	t	2025-10-09 14:37:30.967573+00	\N
3178	1587	2	2025-05-10	RELATIVE	2025-06-13	34	133.30	2	Delivery option 2 for Computer Equipment - Desktop	t	2025-10-09 14:37:30.967573+00	\N
3179	1588	1	2025-03-21	RELATIVE	2025-04-26	36	142.35	1	Delivery option 1 for Network Equipment - Switch/Router	t	2025-10-09 14:37:30.967573+00	\N
3180	1588	2	2025-04-08	RELATIVE	2025-06-05	58	117.99	2	Delivery option 2 for Network Equipment - Switch/Router	t	2025-10-09 14:37:30.967573+00	\N
3181	1589	1	2025-04-20	RELATIVE	2025-05-29	39	166.07	1	Delivery option 1 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3182	1589	2	2025-05-08	RELATIVE	2025-07-22	75	135.46	2	Delivery option 2 for Fine Aggregate - River Sand	t	2025-10-09 14:37:30.967573+00	\N
3183	1590	1	2025-03-16	RELATIVE	2025-06-02	78	137.13	1	Delivery option 1 for Formwork - Steel Panels	t	2025-10-09 14:37:30.967573+00	\N
3184	1590	2	2025-04-02	RELATIVE	2025-05-27	55	113.44	2	Delivery option 2 for Formwork - Steel Panels	t	2025-10-09 14:37:30.967573+00	\N
3185	1591	1	2025-03-03	RELATIVE	2025-05-19	77	102.00	1	Delivery option 1 for Meeting Room Furniture Set	t	2025-10-09 14:37:30.967573+00	\N
3186	1591	2	2025-03-15	RELATIVE	2025-05-02	48	136.37	2	Delivery option 2 for Meeting Room Furniture Set	t	2025-10-09 14:37:30.967573+00	\N
3187	1592	1	2025-05-03	RELATIVE	2025-06-28	56	124.77	1	Delivery option 1 for Coarse Aggregate - 20mm	t	2025-10-09 14:37:30.967573+00	\N
3188	1592	2	2025-05-10	RELATIVE	2025-06-26	47	124.59	2	Delivery option 2 for Coarse Aggregate - 20mm	t	2025-10-09 14:37:30.967573+00	\N
3189	1593	1	2025-03-12	RELATIVE	2025-04-26	45	140.46	1	Delivery option 1 for Marble Tiles - 30x30cm	t	2025-10-09 14:37:30.967573+00	\N
3190	1593	2	2025-03-25	RELATIVE	2025-06-04	71	126.98	2	Delivery option 2 for Marble Tiles - 30x30cm	t	2025-10-09 14:37:30.967573+00	\N
3191	1594	1	2025-05-18	RELATIVE	2025-06-18	31	171.79	1	Delivery option 1 for Aluminum Windows - Double Glazed	t	2025-10-09 14:37:30.967573+00	\N
3192	1594	2	2025-06-03	RELATIVE	2025-08-02	60	169.24	2	Delivery option 2 for Aluminum Windows - Double Glazed	t	2025-10-09 14:37:30.967573+00	\N
3193	1595	1	2025-03-07	RELATIVE	2025-05-23	77	125.86	1	Delivery option 1 for Crane - 50 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3194	1595	2	2025-03-21	RELATIVE	2025-05-02	42	115.81	2	Delivery option 2 for Crane - 50 Ton Capacity	t	2025-10-09 14:37:30.967573+00	\N
3195	1596	1	2025-03-21	RELATIVE	2025-05-10	50	132.48	1	Delivery option 1 for Personal Protective Equipment Set	t	2025-10-09 14:37:30.967573+00	\N
3196	1596	2	2025-03-30	RELATIVE	2025-06-27	89	125.54	2	Delivery option 2 for Personal Protective Equipment Set	t	2025-10-09 14:37:30.967573+00	\N
3197	1597	1	2025-03-03	RELATIVE	2025-05-15	73	152.53	1	Delivery option 1 for Office Furniture - Ergonomic	t	2025-10-09 14:37:30.967573+00	\N
3198	1597	2	2025-03-15	RELATIVE	2025-04-30	46	105.27	2	Delivery option 2 for Office Furniture - Ergonomic	t	2025-10-09 14:37:30.967573+00	\N
3199	1598	1	2025-05-06	RELATIVE	2025-07-11	66	140.10	1	Delivery option 1 for Roofing Tiles - Clay	t	2025-10-09 14:37:30.967573+00	\N
3200	1598	2	2025-05-13	RELATIVE	2025-07-18	66	126.29	2	Delivery option 2 for Roofing Tiles - Clay	t	2025-10-09 14:37:30.967573+00	\N
\.


--
-- Data for Name: finalized_decisions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.finalized_decisions (id, run_id, project_id, project_item_id, item_code, procurement_option_id, purchase_date, delivery_date, quantity, final_cost, status, delivery_option_id, forecast_invoice_timing_type, forecast_invoice_issue_date, forecast_invoice_days_after_delivery, forecast_invoice_amount, actual_invoice_issue_date, actual_invoice_amount, actual_invoice_received_date, invoice_entered_by_id, invoice_entered_at, decision_maker_id, decision_date, finalized_at, finalized_by_id, is_manual_edit, notes, created_at, updated_at, bunch_id, bunch_name) FROM stdin;
\.


--
-- Data for Name: optimization_results; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.optimization_results (id, run_id, run_timestamp, project_id, item_code, procurement_option_id, purchase_time, delivery_time, quantity, final_cost) FROM stdin;
\.


--
-- Data for Name: optimization_runs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.optimization_runs (run_id, run_timestamp, request_parameters, status) FROM stdin;
\.


--
-- Data for Name: procurement_options; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.procurement_options (id, item_code, supplier_name, base_cost, lomc_lead_time, discount_bundle_threshold, discount_bundle_percent, payment_terms, created_at, updated_at, is_active) FROM stdin;
4651	ELEC001	Beta Materials Corp	87.24	7	100	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4652	ELEC001	Mu Construction	93.32	3	50	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4653	ELEC001	Zeta Construction	94.74	6	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4654	CONC003	Beta Materials Corp	106.41	1	25	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4655	CONC003	Eta Materials Ltd	89.49	5	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4656	CONC003	Theta Supply Chain	88.13	6	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4697	ROOF002	Kappa Building Materials	108.18	6	10	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4657	CONC001	Iota Construction Co	102.66	1	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4658	CONC001	Delta Building Solutions	102.96	3	100	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4659	CONC001	Eta Materials Ltd	88.10	2	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4660	EQUIP003	Zeta Construction	99.52	7	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4661	EQUIP003	Lambda Industrial Supply	98.77	6	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4662	EQUIP003	Delta Building Solutions	92.22	6	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4663	TOOL001	Alpha Construction Supply	106.20	7	100	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4664	TOOL001	Delta Building Solutions	113.06	6	50	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4665	TOOL001	Lambda Industrial Supply	103.77	5	10	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4666	FENCE001	Epsilon Procurement	85.32	6	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4667	FENCE001	Zeta Construction	110.43	3	25	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4668	FENCE001	Iota Construction Co	109.12	6	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4669	PLUMB001	Beta Materials Corp	96.04	5	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4670	PLUMB001	Kappa Building Materials	89.31	3	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4671	PLUMB001	Gamma Industrial	96.80	6	50	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4672	LAND002	Delta Building Solutions	88.87	7	25	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4673	LAND002	Zeta Construction	106.94	5	25	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4674	LAND002	Iota Construction Co	99.90	2	50	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4675	AGG001	Alpha Construction Supply	93.75	3	50	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4676	AGG001	Kappa Building Materials	99.32	2	10	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4677	AGG001	Mu Construction	95.74	3	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4678	LAND001	Eta Materials Ltd	85.76	3	25	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4679	LAND001	Alpha Construction Supply	104.20	5	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4680	LAND001	Lambda Industrial Supply	103.68	5	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4681	AGG002	Lambda Industrial Supply	103.14	5	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4682	AGG002	Beta Materials Corp	88.89	4	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4683	AGG002	Theta Supply Chain	91.80	2	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4684	FIRE001	Iota Construction Co	89.85	3	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4685	FIRE001	Delta Building Solutions	102.88	3	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4686	FIRE001	Zeta Construction	101.21	7	50	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4687	CONC002	Delta Building Solutions	111.22	3	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4688	CONC002	Kappa Building Materials	112.67	1	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4689	CONC002	Theta Supply Chain	98.24	3	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4690	WINDOW001	Iota Construction Co	97.59	2	10	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4691	WINDOW001	Epsilon Procurement	109.67	5	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4692	WINDOW001	Delta Building Solutions	103.47	7	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4693	LIGHT001	Alpha Construction Supply	106.53	6	100	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4694	LIGHT001	Delta Building Solutions	105.52	7	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4695	LIGHT001	Theta Supply Chain	101.17	7	100	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4696	ROOF002	Gamma Industrial	111.15	4	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4698	ROOF002	Delta Building Solutions	96.09	5	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4699	HVAC002	Alpha Construction Supply	114.75	4	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4700	HVAC002	Beta Materials Corp	98.90	4	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4701	HVAC002	Iota Construction Co	89.85	6	25	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4702	FORM001	Delta Building Solutions	96.44	4	25	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4703	FORM001	Lambda Industrial Supply	97.79	7	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4704	FORM001	Zeta Construction	100.63	5	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4705	AGG002	Theta Supply Chain	107.91	4	10	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4706	AGG002	Alpha Construction Supply	94.46	2	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4707	AGG002	Iota Construction Co	89.46	1	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4708	FURN002	Alpha Construction Supply	106.12	4	100	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4709	FURN002	Lambda Industrial Supply	110.27	2	10	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4710	FURN002	Beta Materials Corp	112.07	6	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4711	INSUL001	Delta Building Solutions	88.93	2	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4712	INSUL001	Kappa Building Materials	88.40	2	50	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4713	INSUL001	Alpha Construction Supply	100.27	4	10	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4714	EQUIP001	Gamma Industrial	107.27	2	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4715	EQUIP001	Delta Building Solutions	97.33	1	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4716	EQUIP001	Theta Supply Chain	94.91	2	10	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4717	CLEAN001	Zeta Construction	86.95	1	10	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4718	CLEAN001	Beta Materials Corp	112.18	2	25	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4719	CLEAN001	Delta Building Solutions	99.97	6	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4720	SAFETY002	Delta Building Solutions	110.14	5	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4721	SAFETY002	Beta Materials Corp	110.79	5	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4722	SAFETY002	Iota Construction Co	103.24	2	50	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4723	DOOR001	Lambda Industrial Supply	108.82	4	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4724	DOOR001	Eta Materials Ltd	89.45	1	100	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4725	DOOR001	Epsilon Procurement	107.02	3	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4726	MAINT001	Theta Supply Chain	104.90	4	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4727	MAINT001	Epsilon Procurement	110.77	3	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4728	MAINT001	Kappa Building Materials	98.14	7	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4729	LAND001	Zeta Construction	91.95	1	50	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4730	LAND001	Delta Building Solutions	97.93	2	25	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4731	LAND001	Gamma Industrial	91.24	3	100	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4732	STEEL002	Eta Materials Ltd	110.53	4	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4733	STEEL002	Alpha Construction Supply	97.21	1	25	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4734	STEEL002	Iota Construction Co	112.91	6	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4735	SECURITY002	Gamma Industrial	106.01	7	50	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4736	SECURITY002	Epsilon Procurement	93.10	2	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4737	SECURITY002	Theta Supply Chain	111.66	7	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4738	INSUL001	Epsilon Procurement	86.80	6	50	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4739	INSUL001	Theta Supply Chain	93.83	4	100	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4740	INSUL001	Iota Construction Co	94.01	4	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4741	CONC001	Zeta Construction	89.31	5	25	20.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4742	CONC001	Kappa Building Materials	111.52	4	50	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4743	CONC001	Lambda Industrial Supply	102.85	3	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4744	PLUMB002	Beta Materials Corp	97.56	7	50	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4745	PLUMB002	Kappa Building Materials	97.54	5	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4746	PLUMB002	Delta Building Solutions	97.42	4	50	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4747	SECURITY002	Zeta Construction	99.21	4	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4748	SECURITY002	Alpha Construction Supply	104.93	6	100	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4749	SECURITY002	Eta Materials Ltd	86.01	4	25	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4750	PAINT002	Beta Materials Corp	98.77	5	100	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4751	PAINT002	Zeta Construction	98.64	2	25	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4752	PAINT002	Mu Construction	88.40	5	100	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4753	TILE002	Beta Materials Corp	91.45	2	50	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4754	TILE002	Kappa Building Materials	98.23	1	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4755	TILE002	Mu Construction	112.58	5	25	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4756	MAINT001	Alpha Construction Supply	110.16	3	50	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4757	MAINT001	Beta Materials Corp	99.76	4	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4758	MAINT001	Epsilon Procurement	86.53	2	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4759	COMM001	Lambda Industrial Supply	108.88	2	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4760	COMM001	Alpha Construction Supply	100.43	7	10	10.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4761	COMM001	Epsilon Procurement	101.21	2	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4762	EQUIP001	Iota Construction Co	92.84	1	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4763	EQUIP001	Zeta Construction	112.50	1	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4764	EQUIP001	Mu Construction	88.91	2	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4765	IT001	Kappa Building Materials	94.05	6	10	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4766	IT001	Mu Construction	85.78	7	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4767	IT001	Lambda Industrial Supply	94.93	3	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4768	IT002	Lambda Industrial Supply	107.35	2	50	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4769	IT002	Kappa Building Materials	89.38	2	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4770	IT002	Delta Building Solutions	108.99	1	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4771	AGG002	Kappa Building Materials	96.46	7	10	15.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4772	AGG002	Mu Construction	102.52	3	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4773	AGG002	Zeta Construction	114.36	2	50	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4774	FORM001	Kappa Building Materials	95.83	5	100	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4775	FORM001	Iota Construction Co	99.84	3	25	5.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4776	FORM001	Mu Construction	88.38	3	25	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4777	FURN002	Zeta Construction	110.19	3	100	20.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4778	FURN002	Iota Construction Co	109.84	4	25	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4779	FURN002	Theta Supply Chain	98.41	4	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
4780	AGG001	Gamma Industrial	102.47	4	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4781	AGG001	Theta Supply Chain	95.04	5	100	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4782	AGG001	Alpha Construction Supply	95.61	4	10	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4783	TILE002	Mu Construction	104.12	6	25	20.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4784	TILE002	Eta Materials Ltd	98.46	3	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4785	TILE002	Gamma Industrial	112.21	2	100	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4786	WINDOW001	Theta Supply Chain	88.23	7	25	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4787	WINDOW001	Delta Building Solutions	106.96	2	25	15.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4788	WINDOW001	Iota Construction Co	105.40	1	50	10.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 50}, {"due_offset": 1, "percent": 50}]}	2025-10-09 14:37:30.923328+00	\N	t
4789	EQUIP002	Iota Construction Co	111.56	3	25	10.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4790	EQUIP002	Epsilon Procurement	95.79	4	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4791	EQUIP002	Beta Materials Corp	102.02	4	10	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4792	SAFETY002	Gamma Industrial	91.95	1	25	15.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4793	SAFETY002	Mu Construction	98.71	2	25	10.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4794	SAFETY002	Lambda Industrial Supply	107.88	5	25	20.00	{"type": "cash", "discount_percent": 5}	2025-10-09 14:37:30.923328+00	\N	t
4795	FURN001	Zeta Construction	101.94	6	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4796	FURN001	Theta Supply Chain	87.59	2	50	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4797	FURN001	Beta Materials Corp	107.44	7	25	5.00	{"type": "cash", "discount_percent": 2}	2025-10-09 14:37:30.923328+00	\N	t
4798	ROOF001	Kappa Building Materials	85.36	7	10	15.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 30}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 20}, {"due_offset": 3, "percent": 20}]}	2025-10-09 14:37:30.923328+00	\N	t
4799	ROOF001	Delta Building Solutions	101.28	3	50	5.00	{"type": "cash", "discount_percent": 3}	2025-10-09 14:37:30.923328+00	\N	t
4800	ROOF001	Lambda Industrial Supply	90.69	1	100	5.00	{"type": "installments", "schedule": [{"due_offset": 0, "percent": 40}, {"due_offset": 1, "percent": 30}, {"due_offset": 2, "percent": 30}]}	2025-10-09 14:37:30.923328+00	\N	t
\.


--
-- Data for Name: project_assignments; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_assignments (user_id, project_id, assigned_at) FROM stdin;
219	156	2025-10-09 14:37:30.823259+00
220	157	2025-10-09 14:37:30.823259+00
219	158	2025-10-09 14:37:30.823259+00
220	159	2025-10-09 14:37:30.823259+00
219	160	2025-10-09 14:37:30.823259+00
\.


--
-- Data for Name: project_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_items (id, project_id, item_code, item_name, quantity, delivery_options, status, external_purchase, decision_date, procurement_date, payment_date, invoice_submission_date, expected_cash_in_date, actual_cash_in_date, created_at, updated_at) FROM stdin;
1599	160	ELEC001	Electrical Cables - 3-Core 2.5mm²	14	["2025-04-19", "2025-05-05", "2025-05-19"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1600	160	CONC003	Cement - Portland Type I	11	["2025-04-23", "2025-05-11", "2025-06-02", "2025-06-19"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1551	156	CONC001	Ready-Mix Concrete - Grade C25	19	["2025-03-31", "2025-04-21", "2025-05-06"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1552	156	EQUIP003	Concrete Mixer - 3m³	17	["2025-04-28", "2025-05-07", "2025-06-01"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1553	156	TOOL001	Power Tools - Construction Set	20	["2025-03-03", "2025-03-17", "2025-04-04", "2025-03-30"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1554	156	FENCE001	Perimeter Fencing - Chain Link	8	["2025-04-04", "2025-04-24", "2025-05-16"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1555	156	PLUMB001	Water Pipes - PVC 100mm	1	["2025-05-07", "2025-05-17", "2025-06-06", "2025-06-09"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1556	156	LAND002	Irrigation System - Drip Type	7	["2025-03-27", "2025-04-07", "2025-04-10", "2025-05-14"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1557	156	AGG001	Coarse Aggregate - 20mm	6	["2025-05-22", "2025-06-10", "2025-06-15"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1558	156	LAND001	Landscaping - Trees & Shrubs	19	["2025-03-03", "2025-03-14"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1559	156	AGG002	Fine Aggregate - River Sand	19	["2025-03-14", "2025-04-03", "2025-03-28"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1560	156	FIRE001	Fire Extinguishers - 10kg	13	["2025-04-11", "2025-05-02", "2025-05-17", "2025-06-13"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1561	157	CONC002	Ready-Mix Concrete - Grade C30	16	["2025-05-14", "2025-05-25"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1562	157	WINDOW001	Aluminum Windows - Double Glazed	15	["2025-03-22", "2025-04-06"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1563	157	LIGHT001	LED Light Fixtures - Industrial	20	["2025-04-22", "2025-05-13", "2025-05-14"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1564	157	ROOF002	Roofing Membrane - EPDM	9	["2025-03-27", "2025-04-17", "2025-04-24", "2025-05-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1565	157	HVAC002	Ventilation Fans - Industrial	2	["2025-05-30", "2025-06-18", "2025-06-13"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1566	157	FORM001	Formwork - Steel Panels	17	["2025-04-16", "2025-05-03"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1567	157	AGG002	Fine Aggregate - River Sand	18	["2025-05-20", "2025-06-08", "2025-06-11"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1568	157	FURN002	Meeting Room Furniture Set	3	["2025-03-22", "2025-04-01", "2025-04-25", "2025-04-27"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1569	157	INSUL001	Thermal Insulation - Rockwool	16	["2025-03-07", "2025-03-17", "2025-04-04"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1570	157	EQUIP001	Excavator - 20 Ton Capacity	7	["2025-04-08", "2025-04-22", "2025-04-26"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1571	158	CLEAN001	Cleaning Equipment - Industrial	4	["2025-04-30", "2025-05-13"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1572	158	SAFETY002	Personal Protective Equipment Set	1	["2025-05-28", "2025-06-08", "2025-06-19", "2025-07-09"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1573	158	DOOR001	Steel Doors - Fire Rated	12	["2025-03-04", "2025-03-23", "2025-04-11"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1574	158	MAINT001	Maintenance Tools - Complete Set	16	["2025-03-21", "2025-04-01", "2025-04-08", "2025-04-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1575	158	LAND001	Landscaping - Trees & Shrubs	3	["2025-04-01", "2025-04-22"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1576	158	STEEL002	Reinforcement Bars - Grade 60	14	["2025-04-05", "2025-04-26"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1577	158	SECURITY002	Access Control System	14	["2025-05-14", "2025-06-01", "2025-06-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1578	158	INSUL001	Thermal Insulation - Rockwool	16	["2025-03-20", "2025-04-03", "2025-04-27", "2025-05-19"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1579	158	CONC001	Ready-Mix Concrete - Grade C25	20	["2025-05-16", "2025-06-05", "2025-05-30"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1580	158	PLUMB002	Sewage Pipes - HDPE 200mm	4	["2025-03-07", "2025-03-19", "2025-04-06"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1581	159	SECURITY002	Access Control System	1	["2025-03-15", "2025-03-23", "2025-03-29", "2025-04-05"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1582	159	PAINT002	Interior Paint - Low VOC	14	["2025-05-03", "2025-05-23", "2025-05-31", "2025-06-05"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1583	159	TILE002	Marble Tiles - 30x30cm	3	["2025-05-12", "2025-05-30", "2025-06-19", "2025-07-11"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1584	159	MAINT001	Maintenance Tools - Complete Set	18	["2025-05-07", "2025-05-21"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1585	159	COMM001	Communication Equipment - Radio	6	["2025-03-21", "2025-04-04"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1586	159	EQUIP001	Excavator - 20 Ton Capacity	3	["2025-05-13", "2025-06-01"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1587	159	IT001	Computer Equipment - Desktop	10	["2025-04-20", "2025-05-10", "2025-05-24", "2025-06-16"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1588	159	IT002	Network Equipment - Switch/Router	14	["2025-03-21", "2025-04-08", "2025-04-24", "2025-05-14"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1589	159	AGG002	Fine Aggregate - River Sand	11	["2025-04-20", "2025-05-08", "2025-05-22"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1590	159	FORM001	Formwork - Steel Panels	8	["2025-03-16", "2025-04-02"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1591	160	FURN002	Meeting Room Furniture Set	15	["2025-03-03", "2025-03-15"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1592	160	AGG001	Coarse Aggregate - 20mm	14	["2025-05-03", "2025-05-10", "2025-06-04", "2025-06-29"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1593	160	TILE002	Marble Tiles - 30x30cm	5	["2025-03-12", "2025-03-25"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1594	160	WINDOW001	Aluminum Windows - Double Glazed	6	["2025-05-18", "2025-06-03"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1595	160	EQUIP002	Crane - 50 Ton Capacity	14	["2025-03-07", "2025-03-21", "2025-04-14", "2025-05-06"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1596	160	SAFETY002	Personal Protective Equipment Set	8	["2025-03-21", "2025-03-30", "2025-04-26"]	PENDING	f	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1597	160	FURN001	Office Furniture - Ergonomic	13	["2025-03-03", "2025-03-15", "2025-04-10"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
1598	160	ROOF001	Roofing Tiles - Clay	1	["2025-05-06", "2025-05-13"]	PENDING	t	\N	\N	\N	\N	\N	\N	2025-10-09 14:37:30.847151+00	\N
\.


--
-- Data for Name: project_phases; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project_phases (id, project_id, phase_name, start_date, end_date, created_at, updated_at) FROM stdin;
621	156	Phase 1: Planning & Design	2025-01-01	2025-02-15	2025-10-09 14:37:30.835939+00	\N
622	156	Phase 2: Site Preparation	2025-02-16	2025-04-01	2025-10-09 14:37:30.835939+00	\N
623	156	Phase 3: Construction	2025-04-02	2025-06-30	2025-10-09 14:37:30.835939+00	\N
624	156	Phase 4: Finishing & Testing	2025-07-01	2025-08-29	2025-10-09 14:37:30.835939+00	\N
625	157	Phase 1: Planning & Design	2025-03-02	2025-04-16	2025-10-09 14:37:30.835939+00	\N
626	157	Phase 2: Site Preparation	2025-04-17	2025-05-31	2025-10-09 14:37:30.835939+00	\N
627	157	Phase 3: Construction	2025-06-01	2025-08-29	2025-10-09 14:37:30.835939+00	\N
628	157	Phase 4: Finishing & Testing	2025-08-30	2025-10-28	2025-10-09 14:37:30.835939+00	\N
629	158	Phase 1: Planning & Design	2025-05-01	2025-06-15	2025-10-09 14:37:30.835939+00	\N
630	158	Phase 2: Site Preparation	2025-06-16	2025-07-30	2025-10-09 14:37:30.835939+00	\N
631	158	Phase 3: Construction	2025-07-31	2025-10-28	2025-10-09 14:37:30.835939+00	\N
632	158	Phase 4: Finishing & Testing	2025-10-29	2025-12-27	2025-10-09 14:37:30.835939+00	\N
633	159	Phase 1: Planning & Design	2025-06-30	2025-08-14	2025-10-09 14:37:30.835939+00	\N
634	159	Phase 2: Site Preparation	2025-08-15	2025-09-28	2025-10-09 14:37:30.835939+00	\N
635	159	Phase 3: Construction	2025-09-29	2025-12-27	2025-10-09 14:37:30.835939+00	\N
636	159	Phase 4: Finishing & Testing	2025-12-28	2026-02-25	2025-10-09 14:37:30.835939+00	\N
637	160	Phase 1: Planning & Design	2025-08-29	2025-10-13	2025-10-09 14:37:30.835939+00	\N
638	160	Phase 2: Site Preparation	2025-10-14	2025-11-27	2025-10-09 14:37:30.835939+00	\N
639	160	Phase 3: Construction	2025-11-28	2026-02-25	2025-10-09 14:37:30.835939+00	\N
640	160	Phase 4: Finishing & Testing	2026-02-26	2026-04-26	2025-10-09 14:37:30.835939+00	\N
\.


--
-- Data for Name: projects; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.projects (id, project_code, name, priority_weight, created_at, is_active) FROM stdin;
156	INFRA001	Highway Infrastructure Project	9	2025-10-09 14:37:30.815609+00	t
157	BUILD002	Commercial Building Complex	8	2025-10-09 14:37:30.815609+00	t
158	RESI003	Residential Housing Development	7	2025-10-09 14:37:30.815609+00	t
159	INDU004	Industrial Manufacturing Plant	6	2025-10-09 14:37:30.815609+00	t
160	UTIL005	Utilities Infrastructure Upgrade	5	2025-10-09 14:37:30.815609+00	t
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, username, password_hash, role, created_at, is_active) FROM stdin;
218	admin	$2b$12$0CWmmpkyez2QMy.OPhBvW.nMDH.jSUTQbec3j/PVJypBDes0fmDAy	admin	2025-10-09 14:37:30.803053+00	t
219	pm1	$2b$12$GGn4Gr9RnYSnPQHKx647YOE7zEDMtr2Xqm9NIWIWx0l0PQlfgNdMe	pm	2025-10-09 14:37:30.803053+00	t
220	pm2	$2b$12$eJOy2IjRtO1KsjOX5ztw8uJ2cY4r1YQGW/V2cU.crq/w1Pq1MF1ES	pm	2025-10-09 14:37:30.803053+00	t
221	proc1	$2b$12$wBAXSedguNY.lKvm9nJPGeRbsgdYdD4OZb9lz6Zgi/sBEfBNHtO.6	procurement	2025-10-09 14:37:30.803053+00	t
222	proc2	$2b$12$Ojd9IjQQlKmLhE3gmVDaGutqwNb63tmAyLOascinYsCIcGDlcqEaK	procurement	2025-10-09 14:37:30.803053+00	t
223	finance1	$2b$12$mL3de2hfw2xX2aNHOpsNmuPriwuv7Da5oJT2f98khyK.PImqBTXkW	finance	2025-10-09 14:37:30.803053+00	t
224	finance2	$2b$12$dOcOSV9msvaVSEfrS18QOuY7N3yHo3YXvqIQ44QrUe8F0vB0fFxlm	finance	2025-10-09 14:37:30.803053+00	t
\.


--
-- Name: budget_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.budget_data_id_seq', 385, true);


--
-- Name: cashflow_events_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.cashflow_events_id_seq', 384, true);


--
-- Name: decision_factor_weights_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.decision_factor_weights_id_seq', 256, true);


--
-- Name: delivery_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.delivery_options_id_seq', 3200, true);


--
-- Name: finalized_decisions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.finalized_decisions_id_seq', 173, true);


--
-- Name: optimization_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.optimization_results_id_seq', 213, true);


--
-- Name: procurement_options_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.procurement_options_id_seq', 4800, true);


--
-- Name: project_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.project_items_id_seq', 1600, true);


--
-- Name: project_phases_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.project_phases_id_seq', 640, true);


--
-- Name: projects_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.projects_id_seq', 160, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 224, true);


--
-- Name: budget_data budget_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.budget_data
    ADD CONSTRAINT budget_data_pkey PRIMARY KEY (id);


--
-- Name: cashflow_events cashflow_events_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_pkey PRIMARY KEY (id);


--
-- Name: decision_factor_weights decision_factor_weights_factor_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights
    ADD CONSTRAINT decision_factor_weights_factor_name_key UNIQUE (factor_name);


--
-- Name: decision_factor_weights decision_factor_weights_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.decision_factor_weights
    ADD CONSTRAINT decision_factor_weights_pkey PRIMARY KEY (id);


--
-- Name: delivery_options delivery_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options
    ADD CONSTRAINT delivery_options_pkey PRIMARY KEY (id);


--
-- Name: finalized_decisions finalized_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_pkey PRIMARY KEY (id);


--
-- Name: optimization_results optimization_results_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_pkey PRIMARY KEY (id);


--
-- Name: optimization_runs optimization_runs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_runs
    ADD CONSTRAINT optimization_runs_pkey PRIMARY KEY (run_id);


--
-- Name: procurement_options procurement_options_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.procurement_options
    ADD CONSTRAINT procurement_options_pkey PRIMARY KEY (id);


--
-- Name: project_assignments project_assignments_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_pkey PRIMARY KEY (user_id, project_id);


--
-- Name: project_items project_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items
    ADD CONSTRAINT project_items_pkey PRIMARY KEY (id);


--
-- Name: project_phases project_phases_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases
    ADD CONSTRAINT project_phases_pkey PRIMARY KEY (id);


--
-- Name: projects projects_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.projects
    ADD CONSTRAINT projects_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: idx_finalized_decisions_bunch_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_finalized_decisions_bunch_id ON public.finalized_decisions USING btree (bunch_id);


--
-- Name: ix_budget_data_budget_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_budget_data_budget_date ON public.budget_data USING btree (budget_date);


--
-- Name: ix_budget_data_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_budget_data_id ON public.budget_data USING btree (id);


--
-- Name: ix_cashflow_events_event_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_event_date ON public.cashflow_events USING btree (event_date);


--
-- Name: ix_cashflow_events_forecast_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_forecast_type ON public.cashflow_events USING btree (forecast_type);


--
-- Name: ix_cashflow_events_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_id ON public.cashflow_events USING btree (id);


--
-- Name: ix_cashflow_events_is_cancelled; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_cashflow_events_is_cancelled ON public.cashflow_events USING btree (is_cancelled);


--
-- Name: ix_decision_factor_weights_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_decision_factor_weights_id ON public.decision_factor_weights USING btree (id);


--
-- Name: ix_delivery_options_delivery_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_delivery_date ON public.delivery_options USING btree (delivery_date);


--
-- Name: ix_delivery_options_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_id ON public.delivery_options USING btree (id);


--
-- Name: ix_delivery_options_project_item_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_delivery_options_project_item_id ON public.delivery_options USING btree (project_item_id);


--
-- Name: ix_finalized_decisions_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_id ON public.finalized_decisions USING btree (id);


--
-- Name: ix_finalized_decisions_item_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_item_code ON public.finalized_decisions USING btree (item_code);


--
-- Name: ix_finalized_decisions_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_run_id ON public.finalized_decisions USING btree (run_id);


--
-- Name: ix_finalized_decisions_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_finalized_decisions_status ON public.finalized_decisions USING btree (status);


--
-- Name: ix_optimization_results_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_optimization_results_id ON public.optimization_results USING btree (id);


--
-- Name: ix_optimization_results_run_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_optimization_results_run_id ON public.optimization_results USING btree (run_id);


--
-- Name: ix_procurement_options_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_procurement_options_id ON public.procurement_options USING btree (id);


--
-- Name: ix_procurement_options_item_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_procurement_options_item_code ON public.procurement_options USING btree (item_code);


--
-- Name: ix_project_items_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_project_items_id ON public.project_items USING btree (id);


--
-- Name: ix_project_phases_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_project_phases_id ON public.project_phases USING btree (id);


--
-- Name: ix_projects_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_projects_id ON public.projects USING btree (id);


--
-- Name: ix_projects_project_code; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_projects_project_code ON public.projects USING btree (project_code);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_username; Type: INDEX; Schema: public; Owner: postgres
--

CREATE UNIQUE INDEX ix_users_username ON public.users USING btree (username);


--
-- Name: cashflow_events cashflow_events_cancelled_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_cancelled_by_id_fkey FOREIGN KEY (cancelled_by_id) REFERENCES public.users(id);


--
-- Name: cashflow_events cashflow_events_related_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cashflow_events
    ADD CONSTRAINT cashflow_events_related_decision_id_fkey FOREIGN KEY (related_decision_id) REFERENCES public.finalized_decisions(id) ON DELETE CASCADE;


--
-- Name: delivery_options delivery_options_project_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.delivery_options
    ADD CONSTRAINT delivery_options_project_item_id_fkey FOREIGN KEY (project_item_id) REFERENCES public.project_items(id) ON DELETE CASCADE;


--
-- Name: finalized_decisions finalized_decisions_decision_maker_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_decision_maker_id_fkey FOREIGN KEY (decision_maker_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_delivery_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_delivery_option_id_fkey FOREIGN KEY (delivery_option_id) REFERENCES public.delivery_options(id);


--
-- Name: finalized_decisions finalized_decisions_finalized_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_finalized_by_id_fkey FOREIGN KEY (finalized_by_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_invoice_entered_by_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_invoice_entered_by_id_fkey FOREIGN KEY (invoice_entered_by_id) REFERENCES public.users(id);


--
-- Name: finalized_decisions finalized_decisions_procurement_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_procurement_option_id_fkey FOREIGN KEY (procurement_option_id) REFERENCES public.procurement_options(id);


--
-- Name: finalized_decisions finalized_decisions_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: finalized_decisions finalized_decisions_project_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_project_item_id_fkey FOREIGN KEY (project_item_id) REFERENCES public.project_items(id) ON DELETE CASCADE;


--
-- Name: finalized_decisions finalized_decisions_run_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.finalized_decisions
    ADD CONSTRAINT finalized_decisions_run_id_fkey FOREIGN KEY (run_id) REFERENCES public.optimization_runs(run_id);


--
-- Name: optimization_results optimization_results_procurement_option_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_procurement_option_id_fkey FOREIGN KEY (procurement_option_id) REFERENCES public.procurement_options(id);


--
-- Name: optimization_results optimization_results_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.optimization_results
    ADD CONSTRAINT optimization_results_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id);


--
-- Name: project_assignments project_assignments_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_assignments project_assignments_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_assignments
    ADD CONSTRAINT project_assignments_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: project_items project_items_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_items
    ADD CONSTRAINT project_items_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- Name: project_phases project_phases_project_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project_phases
    ADD CONSTRAINT project_phases_project_id_fkey FOREIGN KEY (project_id) REFERENCES public.projects(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict hlvI0xcMHq0TDhrAufENY3TLbfaZ2CgpHOMhsiwoHTzAy4sSlKitDYI7ufwvIRN

