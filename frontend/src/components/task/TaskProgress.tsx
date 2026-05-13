import { useEffect, useRef, useState } from 'react';
import { Progress } from 'antd';
import type { TaskOut } from '../../api/types';
import { statusColors } from '../../theme/tokens';

function AnimatedNumber({ target, duration = 600 }: { target: number; duration?: number }) {
  const [display, setDisplay] = useState(target);
  const startRef = useRef<number>(target);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const start = startRef.current;
    const diff = target - start;
    const startTime = performance.now();

    const tick = (now: number) => {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // easeOutCubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplay(Math.round(start + diff * eased));
      if (progress < 1) {
        rafRef.current = requestAnimationFrame(tick);
      } else {
        startRef.current = target;
      }
    };

    cancelAnimationFrame(rafRef.current);
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [target, duration]);

  return <span>{display}</span>;
}

export function TaskProgress({ task }: { task: TaskOut }) {
  const percent = task.progress_total > 0
    ? Math.round((task.progress_current / task.progress_total) * 100)
    : 0;

  const colors = statusColors[task.status] || statusColors.pending;

  return (
    <div>
      <div
        style={{
          display: 'flex',
          alignItems: 'baseline',
          justifyContent: 'space-between',
          marginBottom: 8,
        }}
      >
        <span style={{ fontSize: 13, color: '#64748b', fontWeight: 500 }}>进度</span>
        <span
          style={{
            fontSize: 24,
            fontWeight: 700,
            color: colors.text,
            fontFamily: 'monospace',
          }}
        >
          <AnimatedNumber target={percent} />%
        </span>
      </div>
      <Progress
        percent={percent}
        strokeColor={colors.dot}
        size={['100%', 8]}
        railColor="#e2e8f0"
        showInfo={false}
        status={task.status === 'failed' ? 'exception' : undefined}
        style={{ transition: 'all 0.5s ease' }}
      />
      <div
        style={{
          fontSize: 12,
          color: '#94a3b8',
          marginTop: 6,
          fontFamily: 'monospace',
          textAlign: 'right',
        }}
      >
        <AnimatedNumber target={task.progress_current} duration={400} /> / {task.progress_total}
      </div>
    </div>
  );
}
