import { readonly, reactive } from 'vue'

interface DemoFrameSnapshotState {
  currentIndex?: number
  pondId?: string
  collectTime?: string
}

const snapshotState = reactive<DemoFrameSnapshotState>({
  currentIndex: undefined,
  pondId: undefined,
  collectTime: undefined
})

export function useDemoFrameSnapshot() {
  const setSnapshot = (payload: DemoFrameSnapshotState) => {
    snapshotState.currentIndex = payload.currentIndex
    snapshotState.pondId = payload.pondId
    snapshotState.collectTime = payload.collectTime
  }

  return {
    snapshot: readonly(snapshotState),
    setSnapshot
  }
}
