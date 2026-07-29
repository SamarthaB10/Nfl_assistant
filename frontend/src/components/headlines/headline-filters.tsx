"use client";

import Image from "next/image";
import {
  type KeyboardEvent,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

import type { HeadlineSourceFilter } from "@/lib/headlines";
import { getNflTeam, NFL_TEAMS } from "@/lib/nfl-teams";

interface HeadlineFiltersProps {
  loading: boolean;
  onSourceChange: (source: HeadlineSourceFilter) => void;
  onSubmit: () => void;
  onTeamChange: (team: string) => void;
  source: HeadlineSourceFilter;
  team: string;
}

interface PickerOption<T extends string> {
  label: string;
  logoUrl?: string;
  value: T;
}

interface FilterPickerProps<T extends string> {
  disabled: boolean;
  label: string;
  onChange: (value: T) => void;
  options: PickerOption<T>[];
  value: T;
}

const PUBLISHER_OPTIONS: PickerOption<HeadlineSourceFilter>[] = [
  { label: "All publishers", value: "ALL" },
  { label: "ESPN", value: "ESPN" },
  { label: "CBS Sports", value: "CBS" },
  { label: "FOX Sports", value: "FOX" },
  { label: "NBC Sports", value: "NBC" },
];

const TEAM_OPTIONS: PickerOption<string>[] = [
  { label: "All NFL teams", value: "ALL" },
  ...NFL_TEAMS.map((team) => ({
    label: team.name,
    logoUrl: getNflTeam(team.code)?.logoUrl,
    value: team.code,
  })),
];

function FilterPicker<T extends string>({
  disabled,
  label,
  onChange,
  options,
  value,
}: FilterPickerProps<T>) {
  const id = useId();
  const rootRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const listboxRef = useRef<HTMLUListElement>(null);
  const selectedIndex = Math.max(
    options.findIndex((option) => option.value === value),
    0,
  );
  const [activeIndex, setActiveIndex] = useState(selectedIndex);
  const [open, setOpen] = useState(false);
  const selected = options[selectedIndex];

  useEffect(() => {
    function closeOnOutsideClick(event: MouseEvent) {
      if (
        rootRef.current &&
        !rootRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", closeOnOutsideClick);
    return () => document.removeEventListener("mousedown", closeOnOutsideClick);
  }, []);

  useEffect(() => {
    if (open) {
      listboxRef.current?.focus();
    }
  }, [open]);

  function selectOption(index: number) {
    onChange(options[index].value);
    setOpen(false);
    triggerRef.current?.focus();
  }

  function openPicker() {
    if (!disabled) {
      setActiveIndex(selectedIndex);
      setOpen(true);
    }
  }

  function handleTriggerKeyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(event.key)) {
      event.preventDefault();
      openPicker();
    }
  }

  function handleListboxKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((current) => (current + 1) % options.length);
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex(
        (current) => (current - 1 + options.length) % options.length,
      );
    } else if (event.key === "Home") {
      event.preventDefault();
      setActiveIndex(0);
    } else if (event.key === "End") {
      event.preventDefault();
      setActiveIndex(options.length - 1);
    } else if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      selectOption(activeIndex);
    } else if (event.key === "Escape" || event.key === "Tab") {
      setOpen(false);
      if (event.key === "Escape") {
        event.preventDefault();
        triggerRef.current?.focus();
      }
    }
  }

  return (
    <div className="headline-filter" ref={rootRef}>
      <span className="headline-filter__label" id={`${id}-label`}>
        {label}
      </span>
      <button
        aria-controls={`${id}-listbox`}
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-label={`${label}: ${selected.label}`}
        className="headline-filter__trigger"
        disabled={disabled}
        onClick={() => (open ? setOpen(false) : openPicker())}
        onKeyDown={handleTriggerKeyDown}
        ref={triggerRef}
        role="combobox"
        type="button"
      >
        <span className="headline-filter__value" id={`${id}-value`}>
          {selected.logoUrl ? (
            <Image
              alt=""
              aria-hidden="true"
              height={28}
              src={selected.logoUrl}
              width={28}
            />
          ) : label === "Team" ? (
            <span aria-hidden="true" className="headline-filter__nfl-mark">
              NFL
            </span>
          ) : null}
          <span>{selected.label}</span>
        </span>
        <span aria-hidden="true" className="headline-filter__chevron">
          ⌄
        </span>
      </button>
      {open ? (
        <ul
          aria-activedescendant={`${id}-option-${activeIndex}`}
          aria-label={label}
          className="headline-filter__listbox"
          id={`${id}-listbox`}
          onKeyDown={handleListboxKeyDown}
          ref={listboxRef}
          role="listbox"
          tabIndex={-1}
        >
          {options.map((option, index) => (
            <li
              aria-selected={option.value === value}
              className={
                index === activeIndex
                  ? "headline-filter__option is-active"
                  : "headline-filter__option"
              }
              id={`${id}-option-${index}`}
              key={option.value}
              onClick={() => selectOption(index)}
              onMouseEnter={() => setActiveIndex(index)}
              role="option"
            >
              {option.logoUrl ? (
                <Image
                  alt=""
                  aria-hidden="true"
                  height={30}
                  src={option.logoUrl}
                  width={30}
                />
              ) : label === "Team" ? (
                <span aria-hidden="true" className="headline-filter__nfl-mark">
                  NFL
                </span>
              ) : null}
              <span>{option.label}</span>
              {option.value === value ? (
                <span aria-hidden="true" className="headline-filter__check">
                  ✓
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}

export function HeadlineFilters({
  loading,
  onSourceChange,
  onSubmit,
  onTeamChange,
  source,
  team,
}: HeadlineFiltersProps) {
  return (
    <form
      className="headline-filters"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit();
      }}
    >
      <FilterPicker
        disabled={loading}
        label="Publisher"
        onChange={onSourceChange}
        options={PUBLISHER_OPTIONS}
        value={source}
      />
      <FilterPicker
        disabled={loading}
        label="Team"
        onChange={onTeamChange}
        options={TEAM_OPTIONS}
        value={team}
      />
      <button disabled={loading} type="submit">
        {loading ? "Updating…" : "Update feed"}
      </button>
    </form>
  );
}
