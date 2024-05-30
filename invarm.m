function newpos = inv(q0,pos)
    qInitial=struct('JointName',{'base_tt' 'lower_joint' 'upper_joint'},'JointPosition',num2cell(q0));
    arm = importrobot('arm.urdf');
    ik = inverseKinematics('RigidBodyTree', arm);
    endEffector = 'endeffector_Link';
    weights = [0, 0, 0, 1, 1, 0];
    new = ik(endEffector,trvec2tform(pos),weights,qInitial);
    newpos=[new(1).JointPosition new(2).JointPosition new(3).JointPosition];
end

