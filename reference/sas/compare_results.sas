/*------------------------------------------------------------------------------------------------
  compare_results.sas - compares an implementation's grades with the expected values (SAS 9.4 or later)

  %ctcval_compare(results=<dataset with RECORD_ID and your grade/term variables>,
                  version=5 | 6, profile=DEFAULT | BESTCASE_ENZYMES | HYPERGLY_NUMERIC_V5 | PRESENT_NOT_LAB |
                                        UNGRADABLE_ZERO | BASELINE_STRICT,
                  gradelow=, gradehigh=, termlow=, termhigh=,    bidirectional designs (LOW and HIGH scales)
                  grade=, term=,                                 single-scale designs (one worst grade per record)
                  id=RECORD_ID, modules=, convdep=Y, prefix=ctcval_, out=ctcval_cmp, print=Y)

  Requires the datasets created by %ctcval_load (prefix=). Grades are numeric 0-4, missing = not graded;
  terms are compared case- and whitespace-insensitively. A record of records.csv that is absent from results=
  is compared as "no grade, no term". modules= limits the comparison to the listed modules (space-separated,
  e.g. modules=CORE BASELINE); convdep=N excludes the records flagged CONVENTION_DEP = Y.

  Output datasets (prefix out=): &out.module (status by module), &out.mismatch (listing), &out.rules
  (coverage and status by criteria RULE_ID of the version), &out.detail (every compared direction),
  &out.record (one row per record). Macro variables ctcval_status (PASS/FAIL), ctcval_records,
  ctcval_mismatches are set for programs that want to test the outcome; a NOTE or WARNING is written to the log.
------------------------------------------------------------------------------------------------*/
%macro ctcval_compare(results=, version=5, profile=DEFAULT, id=RECORD_ID, gradelow=, gradehigh=, termlow=, termhigh=,
                      grade=, term=, modules=, convdep=Y, prefix=ctcval_, out=ctcval_cmp, print=Y);
  %global ctcval_status ctcval_records ctcval_mismatches;
  %local mode terms n ok absent ndup;
  %let ctcval_status=FAIL;
  %let ctcval_records=0;
  %let ctcval_mismatches=0;
  %let profile=%upcase(&profile);
  %if %length(&gradelow) and %length(&gradehigh) %then %let mode=DIRECTIONAL;
  %else %if %length(&grade) %then %let mode=WORST;
  %else %do;
    %put ERROR: ctcval_compare - give either gradelow= and gradehigh= or grade=;
    %return;
  %end;
  %if %length(&results)=0 or not %sysfunc(exist(&results)) %then %do;
    %put ERROR: ctcval_compare - results dataset &results does not exist;
    %return;
  %end;
  %if not %sysfunc(exist(&prefix.records)) or not %sysfunc(exist(&prefix.expectations)) %then %do;
    %put ERROR: ctcval_compare - run ctcval_load first (datasets &prefix.records and &prefix.expectations are needed);
    %return;
  %end;
  %let terms=N;
  %if &mode=DIRECTIONAL and %length(&termlow) and %length(&termhigh) %then %let terms=Y;
  %if &mode=WORST and %length(&term) %then %let terms=Y;

  /* 1. expected values of the version under the profile: DEFAULT rows, overridden by the profile rows */
  proc sort data=&prefix.expectations(where=(VERSION=&version and PROFILE in ('DEFAULT', "&profile"))) out=&out._long;
    by RECORD_ID DIRECTION;
  run;
  data &out._long;
    set &out._long;
    by RECORD_ID DIRECTION;
    retain _g _bg _has;
    length _t $60;
    retain _t;
    if first.DIRECTION then do;
      _has=0;
      call missing(_g, _bg, _t);
    end;
    if PROFILE ne 'DEFAULT' then do;
      _g=GRADE; _bg=BASE_GRADE; _t=TERM; _has=1;
    end;
    else if not _has then do;
      _g=GRADE; _bg=BASE_GRADE; _t=TERM;
    end;
    if last.DIRECTION then do;
      GRADE=_g; BASE_GRADE=_bg; TERM=_t;
      output;
    end;
    drop _g _bg _t _has PROFILE;
  run;
  data &out._exp;
    set &out._long;
    by RECORD_ID;
    length EXP_TERM_LOW EXP_TERM_HIGH EXP_TERM_WORST $60;
    retain EXP_GRADE_LOW EXP_GRADE_HIGH EXP_GRADE_WORST EXP_TERM_LOW EXP_TERM_HIGH EXP_TERM_WORST;
    if first.RECORD_ID then call missing(EXP_GRADE_LOW, EXP_GRADE_HIGH, EXP_GRADE_WORST, EXP_TERM_LOW, EXP_TERM_HIGH, EXP_TERM_WORST);
    select (DIRECTION);
      when ('LOW') do; EXP_GRADE_LOW=GRADE; EXP_TERM_LOW=TERM; end;
      when ('HIGH') do; EXP_GRADE_HIGH=GRADE; EXP_TERM_HIGH=TERM; end;
      when ('WORST') do; EXP_GRADE_WORST=GRADE; EXP_TERM_WORST=TERM; end;
      otherwise;
    end;
    if last.RECORD_ID then output;
    keep RECORD_ID EXP_GRADE_LOW EXP_GRADE_HIGH EXP_GRADE_WORST EXP_TERM_LOW EXP_TERM_HIGH EXP_TERM_WORST;
  run;

  /* 2. the implementation's results under standard names */
  data &out._got;
    set &results;
    length GOT_TERM_LOW GOT_TERM_HIGH GOT_TERM_WORST $200;
    RECORD_ID=&id;
    call missing(GOT_GRADE_LOW, GOT_GRADE_HIGH, GOT_GRADE_WORST, GOT_TERM_LOW, GOT_TERM_HIGH, GOT_TERM_WORST);
    %if &mode=DIRECTIONAL %then %do;
      GOT_GRADE_LOW=&gradelow;
      GOT_GRADE_HIGH=&gradehigh;
      %if &terms=Y %then %do;
        GOT_TERM_LOW=&termlow;
        GOT_TERM_HIGH=&termhigh;
      %end;
    %end;
    %else %do;
      GOT_GRADE_WORST=&grade;
      %if &terms=Y %then %do;
        GOT_TERM_WORST=&term;
      %end;
    %end;
    IN_RESULTS=1;
    keep RECORD_ID GOT_GRADE_LOW GOT_GRADE_HIGH GOT_GRADE_WORST GOT_TERM_LOW GOT_TERM_HIGH GOT_TERM_WORST IN_RESULTS;
  run;
  proc sort data=&out._got nodupkey dupout=&out._dup;
    by RECORD_ID;
  run;
  %let ndup=0;
  data _null_;
    if 0 then set &out._dup nobs=nobs;   /* nobs is set at compile time, also when the dataset is empty */
    call symputx('ndup', nobs);
    stop;
  run;
  %if &ndup>0 %then %put WARNING: ctcval_compare - &ndup duplicate RECORD_ID rows in &results were dropped (first row kept);

  /* 3. one row per record x direction with the comparison flags (STATUS is not kept: naming=SDTM renames it) */
  proc sort data=&prefix.records(keep=RECORD_ID SCENARIO_ID MODULE GRADABLE RULE_IDS CONVENTIONS CONVENTION_DEP DESCRIPTION)
            out=&out._rec;
    by RECORD_ID;
  run;
  data &out.detail;
    merge &out._rec(in=_a) &out._exp &out._got;
    by RECORD_ID;
    if _a;
    %if %length(&modules) %then %do;
      if findw(upcase("&modules"), MODULE, ' ', 'it') > 0;
    %end;
    %if %upcase(&convdep)=N %then %do;
      if CONVENTION_DEP ne 'Y';
    %end;
    if IN_RESULTS ne 1 then IN_RESULTS=0;
    length DIRECTION $5 EXP_TERM GOT_TERM $200;
    %if &mode=DIRECTIONAL %then %do;
      DIRECTION='LOW';
      EXP_GRADE=EXP_GRADE_LOW; GOT_GRADE=GOT_GRADE_LOW; EXP_TERM=EXP_TERM_LOW; GOT_TERM=GOT_TERM_LOW;
      link check;
      output;
      DIRECTION='HIGH';
      EXP_GRADE=EXP_GRADE_HIGH; GOT_GRADE=GOT_GRADE_HIGH; EXP_TERM=EXP_TERM_HIGH; GOT_TERM=GOT_TERM_HIGH;
      link check;
      output;
    %end;
    %else %do;
      DIRECTION='WORST';
      EXP_GRADE=EXP_GRADE_WORST; GOT_GRADE=GOT_GRADE_WORST; EXP_TERM=EXP_TERM_WORST; GOT_TERM=GOT_TERM_WORST;
      link check;
      output;
    %end;
    return;
    check:
      GRADE_OK=((missing(EXP_GRADE) and missing(GOT_GRADE)) or (not missing(EXP_GRADE) and not missing(GOT_GRADE) and EXP_GRADE=GOT_GRADE));
      %if &terms=Y %then %do;
        TERM_OK=(compress(upcase(EXP_TERM))=compress(upcase(GOT_TERM)));
      %end;
      %else %do;
        TERM_OK=1;
      %end;
      OK=(GRADE_OK and TERM_OK);
    return;
    keep RECORD_ID SCENARIO_ID MODULE GRADABLE RULE_IDS CONVENTIONS CONVENTION_DEP DESCRIPTION
         DIRECTION EXP_GRADE GOT_GRADE EXP_TERM GOT_TERM GRADE_OK TERM_OK OK IN_RESULTS;
  run;

  /* 4. record level, module summary, mismatch listing, rule coverage */
  proc sql noprint;
    create table &out.record as
      select RECORD_ID, SCENARIO_ID, MODULE, RULE_IDS, CONVENTION_DEP, IN_RESULTS, min(OK) as OK
      from &out.detail
      group by RECORD_ID, SCENARIO_ID, MODULE, RULE_IDS, CONVENTION_DEP, IN_RESULTS
      order by RECORD_ID;
    create table &out.module as
      select MODULE, count(*) as RECORDS, sum(OK) as AGREE, count(*)-sum(OK) as MISMATCHES,
             sum(IN_RESULTS=0) as NOT_IN_RESULTS,
             case when count(*)=sum(OK) then 'PASS' else 'FAIL' end as STATUS length=4
      from &out.record
      group by MODULE
      order by MODULE;
    select count(*), sum(OK), sum(IN_RESULTS=0) into :n trimmed, :ok trimmed, :absent trimmed
      from &out.record;
  quit;
  %if &n=0 %then %do;
    %put WARNING: ctcval_compare - no record selected (check modules= and convdep=);
    %return;
  %end;
  data &out.mismatch;
    set &out.detail;
    where OK=0;
  run;
  data &out._rules;
    set &out.record;
    length RULE_ID $24;
    do _i=1 to countw(RULE_IDS, ' ');
      RULE_ID=scan(RULE_IDS, _i, ' ');
      if upcase(substr(RULE_ID, 1, 2))="V&version" then output;
    end;
    keep RULE_ID RECORD_ID OK;
  run;
  proc sql;
    create table &out.rules as
      select c.RULE_ID, c.CTCAE_TERM, c.GRADE, coalesce(r.RECORDS, 0) as RECORDS, coalesce(r.MISMATCHES, 0) as MISMATCHES,
             case when calculated RECORDS=0 then 'NONE' when calculated MISMATCHES=0 then 'PASS' else 'FAIL' end as STATUS length=4
      from (select distinct RULE_ID, CTCAE_TERM, GRADE from &prefix.criteria where VERSION=&version and LAB_DERIVABLE='Y') as c
      left join (select RULE_ID, count(*) as RECORDS, count(*)-sum(OK) as MISMATCHES from &out._rules group by RULE_ID) as r
      on c.RULE_ID=r.RULE_ID
      order by c.RULE_ID;
  quit;
  proc datasets lib=work nolist;
    delete &out._long &out._exp &out._got &out._dup &out._rec &out._rules;
  run;
  quit;

  /* 5. report */
  %let ctcval_records=&n;
  %let ctcval_mismatches=%eval(&n-&ok);
  %if &ctcval_mismatches=0 %then %let ctcval_status=PASS;
  %if %upcase(&print)=Y %then %do;
    title "ctcval_compare - CTCAE v&version profile &profile - status by module";
    proc print data=&out.module noobs;
    run;
    title "ctcval_compare - CTCAE v&version profile &profile - mismatches (expected vs obtained)";
    proc print data=&out.mismatch noobs;
      var RECORD_ID SCENARIO_ID MODULE DIRECTION EXP_GRADE GOT_GRADE EXP_TERM GOT_TERM RULE_IDS CONVENTIONS DESCRIPTION;
    run;
    title "ctcval_compare - CTCAE v&version - criteria rules with a mismatch or without a compared record";
    proc print data=&out.rules noobs;
      where STATUS ne 'PASS';
    run;
    title;
  %end;
  %if &ctcval_status=PASS %then
    %put NOTE: ctcval_compare - PASS &ok of &n records agree with CTCAE v&version profile &profile (&absent records absent from &results);
  %else
    %put WARNING: ctcval_compare - FAIL &ctcval_mismatches of &n records differ from CTCAE v&version profile &profile (&absent absent from &results) - see &out.mismatch;
%mend ctcval_compare;
